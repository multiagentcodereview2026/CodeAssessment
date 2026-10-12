import React from 'react';
import { AlertTriangle, Lightbulb } from 'lucide-react';

type CompilerFeedbackProps = { diagnostics: string };

function explainCompilerDiagnostic(diagnostics: string) {
  const firstError = diagnostics.split(/\r?\n/).find((line) =>
    /(?:\berror\s*:|syntaxerror\s*:|fatal error\s*:)/i.test(line)
  ) || diagnostics.split(/\r?\n/).find((line) => line.trim()) || '';
  const location = diagnostics.match(/(?:solution\.(?:cpp|cc|c|py)|main\.java|<stdin>):(\d+)(?::(\d+))?/i)
    || diagnostics.match(/line\s+(\d+)(?:,\s*column\s+(\d+))?/i);
  const line = location?.[1] ? Number(location[1]) : null;
  const column = location?.[2] ? Number(location[2]) : null;
  const message = firstError.replace(/^.*?(?:error\s*:|syntaxerror\s*:|fatal error\s*:)/i, '').trim();
  const lower = message.toLowerCase();

  let explanation = 'The compiler could not build this program. Start with the first reported error; later messages may be caused by the same issue.';
  let suggestion = 'Check the highlighted line and the line immediately before it for a missing symbol, extra character, or unfinished statement.';

  if (/expected\s+['`]?;|missing\s+semicolon/.test(lower)) {
    explanation = 'A statement appears to be missing a semicolon.';
    suggestion = 'Add a semicolon at the end of the statement just before the reported location.';
  } else if (/expected\s+['`]?\)|expected\s+['`]?\}|expected\s+['`]?\]|unmatched|unclosed/.test(lower)) {
    explanation = 'A bracket, parenthesis, or brace is missing or out of place.';
    suggestion = 'Match each opening `(`, `{`, or `[` with its closing character, and check the nearby lines.';
  } else if (/not declared|undeclared|cannot find symbol|unknown identifier/.test(lower)) {
    explanation = 'The code uses a name the compiler cannot find.';
    suggestion = 'Check the spelling and capitalization, and make sure the variable or function is declared in this scope before it is used.';
  } else if (/expected expression|expected primary-expression|invalid syntax|unexpected token/.test(lower)) {
    explanation = 'The compiler found an incomplete or invalid expression.';
    suggestion = 'Check the operators and values on this line, then look for a missing parenthesis or comma.';
  } else if (/indentation|unexpected indent/.test(lower)) {
    explanation = 'The indentation does not match the language’s block structure.';
    suggestion = 'Align this line with the other statements in its block and use consistent indentation.';
  } else if (/no matching function|cannot convert|incompatible types|type mismatch/.test(lower)) {
    explanation = 'A value or function argument has a type the compiler does not expect.';
    suggestion = 'Compare the value’s type with the function parameter or assignment target, and convert it if needed.';
  }

  return { line, column, message: message || firstError.trim(), explanation, suggestion };
}

export const CompilerFeedback: React.FC<CompilerFeedbackProps> = ({ diagnostics }) => {
  const feedback = explainCompilerDiagnostic(diagnostics);

  return (
    <section className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-rose-950" aria-live="polite">
      <div className="flex items-center gap-2 text-sm font-bold">
        <AlertTriangle className="h-4 w-4 shrink-0 text-rose-600" />
        Compiler feedback{feedback.line ? ` · near line ${feedback.line}${feedback.column ? `, column ${feedback.column}` : ''}` : ''}
      </div>
      <p className="mt-2 text-sm font-semibold">{feedback.explanation}</p>
      <p className="mt-1 flex gap-1.5 text-sm text-rose-900">
        <Lightbulb className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
        <span>{feedback.suggestion}</span>
      </p>
      <details className="mt-3 rounded-lg border border-rose-200 bg-white/70 px-3 py-2">
        <summary className="cursor-pointer text-xs font-semibold text-rose-800">Show compiler details</summary>
        <pre className="mt-2 max-h-48 overflow-auto whitespace-pre-wrap break-words font-mono text-xs leading-5 text-slate-700">{diagnostics || feedback.message}</pre>
      </details>
    </section>
  );
};
