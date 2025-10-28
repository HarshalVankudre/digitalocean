import React, { useMemo } from "react";
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
  isStreaming,
}: {
  role: "user" | "assistant" | string;
  content: string;
  isStreaming?: boolean;
}) {
  // When streaming, only render complete paragraphs/blocks to avoid broken markdown
  const processedContent = useMemo(() => {
    if (!isStreaming) return content;

    // Split by double newlines (paragraphs)
    const blocks = content.split(/\n\n/);

    // Keep all complete blocks, exclude the last incomplete one if it doesn't end with \n\n
    if (blocks.length > 1 && !content.endsWith('\n\n')) {
      const completeBlocks = blocks.slice(0, -1).join('\n\n');
      const incompleteBlock = blocks[blocks.length - 1];
      return { complete: completeBlocks, incomplete: incompleteBlock };
    }

    return { complete: content, incomplete: '' };
  }, [content, isStreaming]);

  const renderedContent = useMemo(() => {
    const contentToRender = typeof processedContent === 'string'
      ? processedContent
      : processedContent.complete;

    return (
      <ReactMarkdown
        className="prose prose-slate max-w-none break-words [&_code]:break-words [&_pre]:whitespace-pre-wrap"
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeRaw, rehypeSanitize, rehypeKatex, rehypeHighlight]}
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
        {contentToRender}
      </ReactMarkdown>
    );
  }, [processedContent]);

  const incompleteText = typeof processedContent !== 'string' ? processedContent.incomplete : '';

  return (
    <div className={`mb-4 ${role === "user" ? "text-slate-900" : "text-slate-800"}`}>
      <div
        className={`rounded-2xl px-4 py-3 shadow-sm ${
          role === "user" ? "bg-white" : "bg-slate-50"
        }`}
      >
        {renderedContent}
        {isStreaming && incompleteText && (
          <div className="text-slate-600 whitespace-pre-wrap mt-2">
            {incompleteText}
            <span className="inline-block w-2 h-4 bg-slate-400 animate-pulse ml-1" />
          </div>
        )}
        {isStreaming && !incompleteText && (
          <span className="inline-block w-2 h-4 bg-slate-400 animate-pulse ml-1" />
        )}
      </div>
    </div>
  );
}