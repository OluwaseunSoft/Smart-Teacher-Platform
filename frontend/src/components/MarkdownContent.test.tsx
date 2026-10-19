import { render } from "@testing-library/react";

import MarkdownContent from "./MarkdownContent";

describe("MarkdownContent", () => {
  it("sets text direction independently for each paragraph", () => {
    const { container } = render(
      <div dir="auto" className="prose-lesson">
        <MarkdownContent>
          {"English introduction.\n\nهذه فقرة باللغة العربية."}
        </MarkdownContent>
      </div>,
    );
    const paragraphs = container.querySelectorAll("p");

    expect(paragraphs).toHaveLength(2);
    expect(paragraphs[0]).toHaveAttribute("dir", "auto");
    expect(paragraphs[1]).toHaveAttribute("dir", "auto");
  });

  it("gives headings and list items independent direction while keeping code LTR", () => {
    const { container } = render(
      <MarkdownContent>{"## ملخّص الدرس\n\n- نقطة عربية\n- English point\n\n> اقتباس عربي\n\n```python\nprint('hello')\n```"}</MarkdownContent>,
    );
    for (const block of container.querySelectorAll("h2, ul, li, blockquote, p")) {
      expect(block).toHaveAttribute("dir", "auto");
    }
    expect(container.querySelectorAll("li")).toHaveLength(2);
    expect(container.querySelector("pre")).toHaveAttribute("dir", "ltr");
  });
});
