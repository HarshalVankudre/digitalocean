// frontend/src/components/ChatMessage.tsx
import React from "react";
import ReactMarkdown from "react-markdown"; // Your original library is fine
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeRaw from "rehype-raw";
import rehypeSanitize from "rehype-sanitize";
import rehypeKatex from "rehype-katex";
import rehypeHighlight from "rehype-highlight";

export default function ChatMessage({
  role,
  content,
  isStreaming,
}: {
  role: "user" | "assistant" | string;
  content: string;
  isStreaming?: boolean;
}) {
  // REMOVED all the 'processedContent' and 'useMemo' logic.
  // We will pass the 'content' prop directly to ReactMarkdown.

  return (
    <div className={`mb-4 ${role === "user" ? "text-slate-900" : "text-slate-800"}`}>
      <div
        className={`rounded-2xl px-4 py-3 shadow-sm ${
          role === "user" ? "bg-white" : "bg-slate-50"
        }`}
      >
        <ReactMarkdown
          className="prose prose-slate max-w-none break-words [&_code]:break-words [&_pre]:whitespace-pre-wrap"
          remarkPlugins={[remarkGfm, remarkMath]}
          rehypePlugins={[rehypeRaw, rehypeSanitize, rehypeKatex, rehypeHighlight]}
          components={{
            // Your custom styles are great
            table: ({ node, ...props }) => (
              <div className="overflow-x-auto">
                <table className="min-w-full table-auto border-collapse" {...props} />
              </div>
            ),
            th: (props) => <th className="border px-3 py-2 bg-slate-100" {...props} />,
            td: (props) => <td className="border px-3 py-2 align-top" {...props} />,
            pre: (props) => (
              <pre className="rounded-lg bg-slate-900/95 p-3 text-slate-50 overflow-x-auto" {...props} />
            ),
            code: (props) => <code className="rounded bg-slate-100 px-1 py-0.5" {...props} />,
          }}
        >
          {content}
        </ReactMarkdown>

        {/* The cursor now just appears at the end if streaming is active */}
        {isStreaming && (
          <span className="inline-block w-2 h-4 bg-slate-400 animate-pulse ml-1" />
        )}
      </div>
    </div>
  );
}