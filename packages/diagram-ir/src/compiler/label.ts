const MAX_LINE_LENGTH = 18;
const MAX_LINES = 2;
const ELLIPSIS = "...";

export function wrapLabel(label: string): string[] {
  const normalized = label.trim().replace(/\s+/g, " ");
  const wrappedLines = normalized.includes(" ")
    ? wrapWords(normalized.split(" "))
    : splitLongToken(normalized);

  if (wrappedLines.length <= MAX_LINES) {
    return wrappedLines;
  }

  return [wrappedLines[0]!, truncateWithEllipsis(wrappedLines[1]!)];
}

function wrapWords(words: string[]): string[] {
  const lines: string[] = [];
  let currentLine = "";

  for (const word of words) {
    if (word.length > MAX_LINE_LENGTH) {
      if (currentLine.length > 0) {
        lines.push(currentLine);
        currentLine = "";
      }

      lines.push(...splitLongToken(word));
      continue;
    }

    if (currentLine.length === 0) {
      currentLine = word;
      continue;
    }

    const candidate = `${currentLine} ${word}`;

    if (candidate.length <= MAX_LINE_LENGTH) {
      currentLine = candidate;
    } else {
      lines.push(currentLine);
      currentLine = word;
    }
  }

  if (currentLine.length > 0) {
    lines.push(currentLine);
  }

  return lines;
}

function splitLongToken(token: string): string[] {
  const chunks: string[] = [];

  for (let index = 0; index < token.length; index += MAX_LINE_LENGTH) {
    chunks.push(token.slice(index, index + MAX_LINE_LENGTH));
  }

  return chunks.length > 0 ? chunks : [""];
}

function truncateWithEllipsis(line: string): string {
  const prefixLength = MAX_LINE_LENGTH - ELLIPSIS.length;
  return `${line.slice(0, prefixLength).trimEnd()}${ELLIPSIS}`;
}
