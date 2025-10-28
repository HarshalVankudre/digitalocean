import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeRaw from "rehype-raw";
import rehypeSanitize from "rehype-sanitize";
import rehypeKatex from "rehype-katex";
import rehypeHighlight from "rehype-highlight";

export default function ChatMessage({
  role,
  content,
}: {
  role: "user" | "assistant" | string;
  content: string;
}) {
  return (
    <div className={`mb-4 ${role === "user" ? "text-slate-900" : "text-slate-800"}`}>
      <div
        className={`rounded-2xl px-4 py-3 shadow-sm ${
          role === "user" ? "bg-white" : "bg-slate-50"
        }`}
      >
        <ReactMarkdown
          // Typography & prevent truncation
          className="prose prose-slate max-w-none break-words [&_code]:break-words [&_pre]:whitespace-pre-wrap"
          // Plugins: tables, math, raw html, sanitize, code highlight
          remarkPlugins={[remarkGfm, remarkMath]}
          rehypePlugins={[rehypeRaw, rehypeSanitize, rehypeKatex, rehypeHighlight]}
          // Map some elements for nicer Tailwind styling
          components={{
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
      </div>
    </div>
  );
}
