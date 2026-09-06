import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <article>
      <h1 className="page-title">Page not found</h1>
      <p>That route is not part of the observatory.</p>
      <p>
        <Link to="/">Return to overview</Link>
      </p>
    </article>
  );
}
