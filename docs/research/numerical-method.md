# Numerical Method — Planar Truss Direct Stiffness

This document describes the FEM formulation **as implemented** in `backend/app/scientific/fem/`. It is not an independent derivation that the code is allowed to drift from.

## Kinematics

Each member is a two-node linear-elastic truss element. It carries axial force only. There is no bending stiffness, no geometric nonlinearity, and no plasticity.

Two displacement DOFs exist at each node: \(u_x\), \(u_y\). Node IDs are sorted; the 0-based index of node \(n\) in that sorted list is \(p\). Then:

\[
\mathrm{dof}_{u_x}(n) = 2p, \qquad \mathrm{dof}_{u_y}(n) = 2p+1
\]

For the canonical 10-bar model, node IDs are \(1\ldots 6\), giving 12 global DOFs numbered \(0\ldots 11\). Supports at nodes 5 and 6 restrain both directions, so constrained DOFs are \(8,9,10,11\) and free DOFs are \(0\ldots 7\).

## Element stiffness

For member \(e\) from node \(i\) to node \(j\):

\[
\Delta x = x_j - x_i,\quad
\Delta y = y_j - y_i,\quad
L = \sqrt{\Delta x^2 + \Delta y^2},\quad
c = \Delta x/L,\quad
s = \Delta y/L
\]

Axial stiffness \(k = A_e E / L\). The 4×4 matrix in global axes is the rank-1 form

\[
k_e = k\, a a^\top, \qquad a = [c,\, s,\, -c,\, -s]^\top
\]

which is identically the textbook expansion

\[
k_e = \frac{A_e E}{L}
\begin{bmatrix}
c^2 & cs & -c^2 & -cs \\
cs & s^2 & -cs & -s^2 \\
-c^2 & -cs & c^2 & cs \\
-cs & -s^2 & cs & s^2
\end{bmatrix}.
\]

Production code implements only the rank-1 form (`fem/element.py`). The expanded form is used in tests as a check, not as a second production path.

## Assembly

Global \(K\) is zero-initialized and each \(k_e\) is scattered into the four global DOFs of the member. Global \(F\) is assembled from the canonical load specification: magnitude \(F\) times the unit direction at the specified node. Load placement is not hard-coded in the solver.

## Boundary conditions

Constrained DOFs are **eliminated**. The production path does not zero rows and columns of \(K\). The reduced system is

\[
K_{ff} u_f = F_f
\]

with constrained displacements identically zero (no non-zero prescribed displacements in Phase 1).

## Linear solve

`numpy.linalg.solve` is used on \(K_{ff}\). An explicit inverse is not formed. Before the solve, `numpy.linalg.cond` is computed. If it is non-finite or exceeds `max_condition_number = 1e12`, the structure is rejected as singular/ill-conditioned. `LinAlgError` is converted to `SingularStructureError`.

The full displacement vector is reconstructed by inserting \(u_f\) into the free DOFs.

## Reactions and equilibrium

\[
R = K u - F
\]

On free DOFs, \(R \approx 0\). On supports, \(R\) is the reaction. Global equilibrium requires

\[
\sum F_x + \sum R_x \approx 0, \qquad
\sum F_y + \sum R_y \approx 0, \qquad
\sum (x R_y - y R_x) + \sum (x F_y - y F_x) \approx 0
\]

within the documented relative tolerances. These checks run inside `analyze()`; a result object with `validated=True` has already passed them.

## Member force, stress, displacement, compliance

Axial extension uses the same direction cosines as the stiffness:

\[
\delta_e = (u_j - u_i)\cdot (c, s), \qquad
N_e = \frac{A_e E}{L_e}\delta_e, \qquad
\sigma_e = N_e / A_e.
\]

Tension (elongation) is positive.

\[
u_{\max} = \max_i \sqrt{u_{x,i}^2 + u_{y,i}^2}, \qquad
\sigma_{\max} = \max_e |\sigma_e|, \qquad
C = F^\top u.
\]

## Units

Internal arithmetic: mm, N, mm², N/mm², N·mm. Paper-facing \(E\) (GPa) and \(F\) (kN) are converted at the parameter boundary by the named factors 1000.

## Independent reference

`tests/scientific/reference_solver.py` uses \(T^\top k_{\mathrm{local}} T\) with \(k_{\mathrm{local}} = (AE/L)[[1,-1],[-1,1]]\), solves with `numpy.linalg.lstsq`, and recovers force from \(\sigma = E \varepsilon\). Production never imports it.

## Tolerances

See `docs/research/paper-a-specification.md` §9 and `configs/scientific.yaml`. They are physical/numerical justifications, not knobs for making tests pass.
