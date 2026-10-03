import { isRouteErrorResponse, Link, useRouteError } from "react-router";
import { errorMessage } from "../api/errors";

export function RouteError() {
  const error = useRouteError();
  const message = isRouteErrorResponse(error)
    ? `${error.status} ${error.statusText}`
    : errorMessage(error);
  return (
    <div role="alert" className="p-6">
      <h1 className="text-xl font-semibold">Something went wrong</h1>
      <p className="mt-2">{message}</p>
      <Link to="/" className="mt-4 inline-block underline">
        Back to games
      </Link>
    </div>
  );
}
