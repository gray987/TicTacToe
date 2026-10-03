interface Props {
  message: string;
  onRetry?: () => void;
}

export function ErrorMessage({ message, onRetry }: Props) {
  return (
    <div role="alert" className="rounded border-2 border-red-700 p-4">
      <p>
        <strong>Error: </strong>
        {message}
      </p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 rounded border-2 border-slate-900 px-3 py-1 font-medium"
        >
          Retry
        </button>
      )}
    </div>
  );
}
