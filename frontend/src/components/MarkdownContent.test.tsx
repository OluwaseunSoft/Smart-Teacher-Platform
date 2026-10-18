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
});
