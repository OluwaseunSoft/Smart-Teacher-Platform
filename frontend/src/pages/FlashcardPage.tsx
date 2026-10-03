import { useState } from "react";

import { Button, Card } from "../components/ui";

const SAMPLE_CARDS = [
  {
    id: 1,
    front: "What is the main idea of a ratio?",
    back: "A ratio compares two quantities and is often written as a:b or a/b.",
  },
  {
    id: 2,
    front: "How can you check if a fraction is equivalent?",
    back: "Multiply or divide the numerator and denominator by the same non-zero number.",
  },
  {
    id: 3,
    front: "What does a negative exponent mean?",
    back: "It means the reciprocal of the positive exponent: a^-n = 1 / a^n.",
  },
];

export default function FlashcardPage() {
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);

  const card = SAMPLE_CARDS[index];

  const nextCard = () => {
    setFlipped(false);
    setIndex((prev) => (prev + 1) % SAMPLE_CARDS.length);
  };

  const handleRating = (rating: "again" | "good" | "easy") => {
    if (rating === "easy") {
      setIndex((prev) => (prev + 1) % SAMPLE_CARDS.length);
      setFlipped(false);
      return;
    }
    setIndex((prev) => (prev + 1) % SAMPLE_CARDS.length);
    setFlipped(false);
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold">Flashcard session</h1>
        <p className="text-slate-600">Review key ideas and rate your recall.</p>
      </header>

      <Card className="min-h-[300px] p-6">
        <div className="mb-4 flex items-center justify-between text-sm text-slate-500">
          <span>Card {index + 1} of {SAMPLE_CARDS.length}</span>
          <span>{flipped ? "Answer" : "Prompt"}</span>
        </div>

        <button
          type="button"
          onClick={() => setFlipped((prev) => !prev)}
          className="flex min-h-[220px] w-full items-center justify-center rounded-xl border border-slate-200 bg-slate-50 p-6 text-left text-lg font-medium text-slate-800 transition hover:border-indigo-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          aria-label={flipped ? "Show prompt" : "Reveal answer"}
        >
          <span className="text-center">{flipped ? card.back : card.front}</span>
        </button>
      </Card>

      <div className="flex flex-wrap gap-3">
        <Button variant="secondary" onClick={() => setFlipped((prev) => !prev)}>
          {flipped ? "Show prompt" : "Reveal answer"}
        </Button>
        <Button onClick={nextCard}>Skip</Button>
      </div>

      <div className="space-y-2">
        <p className="text-sm font-medium text-slate-700">How well did you recall it?</p>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" onClick={() => handleRating("again")}>Again</Button>
          <Button variant="secondary" onClick={() => handleRating("good")}>Good</Button>
          <Button variant="secondary" onClick={() => handleRating("easy")}>Easy</Button>
        </div>
      </div>
    </div>
  );
}
