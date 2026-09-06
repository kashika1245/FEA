export function MethodologyPage() {
  return (
    <article>
      <p className="page-kicker">Protocol</p>
      <h1 className="page-title">Scientific methodology</h1>
      <section className="card">
        <h2>Dataset</h2>
        <p>10,000 FEM-generated samples. Train 7000 / validation 1500 / interpolation test 1500.</p>
        <p>
          Inputs A1–A10 (mm²), E (GPa), F (kN). Outputs u_max (mm), sigma_max (N/mm²), C (N·mm).
          Internal FEM units remain mm, N, mm², N/mm², N·mm. This page does not convert GPa↔N/mm²
          or kN↔N.
        </p>
      </section>
      <section className="card" style={{ marginTop: 12 }}>
        <h2>Surrogate</h2>
        <p>MLP 12→128→128→128→3, ReLU, MSE, Adam, train-only z-score normalization, five seeds retained.</p>
      </section>
      <section className="card" style={{ marginTop: 12 }}>
        <h2>Extrapolation</h2>
        <p>
          One variable is moved at a time beyond the training-domain bound. Distance δ is the
          Phase 2 normalized distance from the bound toward the exterior, on the stored grid
          0.00–0.50. Directions lower and upper are independent. Profiles are median and IQR
          across anchors. Thresholds are first observed 5% and 10% crossings on that grid.
        </p>
        <p>Combined experiment: A3 and F moved together on the same discrete grid.</p>
      </section>
      <section className="card" style={{ marginTop: 12 }}>
        <h2>Limitations</h2>
        <ul>
          <li>One truss benchmark.</li>
          <li>Linear static FEM.</li>
          <li>Synthetic dataset.</li>
          <li>One MLP architecture.</li>
          <li>Finite extrapolation range.</li>
          <li>Empirical threshold conventions, not continuous boundaries.</li>
          <li>One-dimensional profiles do not define a full multidimensional validity domain.</li>
          <li>A3+F is one combined-variable experiment, not a complete multidimensional domain.</li>
          <li>Empirical 5% and 10% crossings are conventions, not continuous safety limits.</li>
          <li>Negative F, if reached, is a mathematical load reversal, not a new physical load case.</li>
          <li>Results should not be generalized to all structures or surrogate architectures.</li>
          <li>No universal validity boundary is claimed.</li>
        </ul>
      </section>
    </article>
  );
}
