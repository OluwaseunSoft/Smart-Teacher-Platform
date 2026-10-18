import ReactMarkdown, { type Components } from "react-markdown";

const components: Components = {
  p: ({ node: _node, ...props }) => <p {...props} dir="auto" />,
};

export default function MarkdownContent({ children }: { children: string }) {
  return <ReactMarkdown components={components}>{children}</ReactMarkdown>;
}
