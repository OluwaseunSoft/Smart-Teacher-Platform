import ReactMarkdown, { type Components } from "react-markdown";

const components: Components = {
  p: ({ node: _node, ...props }) => <p {...props} dir="auto" />,
  h1: ({ node: _node, ...props }) => <h1 {...props} dir="auto" />,
  h2: ({ node: _node, ...props }) => <h2 {...props} dir="auto" />,
  h3: ({ node: _node, ...props }) => <h3 {...props} dir="auto" />,
  h4: ({ node: _node, ...props }) => <h4 {...props} dir="auto" />,
  h5: ({ node: _node, ...props }) => <h5 {...props} dir="auto" />,
  h6: ({ node: _node, ...props }) => <h6 {...props} dir="auto" />,
  ul: ({ node: _node, ...props }) => <ul {...props} dir="auto" />,
  ol: ({ node: _node, ...props }) => <ol {...props} dir="auto" />,
  li: ({ node: _node, ...props }) => <li {...props} dir="auto" />,
  blockquote: ({ node: _node, ...props }) => <blockquote {...props} dir="auto" />,
  pre: ({ node: _node, ...props }) => <pre {...props} dir="ltr" />,
};

export default function MarkdownContent({ children }: { children: string }) {
  return <ReactMarkdown components={components}>{children}</ReactMarkdown>;
}
