# Experimento: banda de crecimiento mínimo + holgura

Seed `configs/base.yaml` · C12 consensuado = 55.8 clientes · MoM del plan año 1 = 15.8%/mes · `scripts/growth_band_experiment.py`

Banda: `stock_t >= B_t` y (si aplica) `stock_t <= B_t·(1+slack_t)`, con `B_t = C12·(1+g_m)^(t-12)`.

| variante | g anual | status | VAN | Ing Y3 | stock m24/m36 | V m13→24→36 | min caja |
|---|---:|---|---:|---:|---|---|---:|
| band-fixed | 1.00 | Optimal | 2,542 | 525,504 | 128/256 | 2→2→3 | -34,823 |
| band-grow | 1.00 | Optimal | 55,847 | 589,564 | 123/289 | 2→2→3 | -39,823 |
| band-mom | 4.79 | Optimal | 2,797,480 | 3,323,593 | 371/2148 | 2→8→41 | -15,793 |
| band-min-only | 1.0 | **Unbounded** | | | | | |
| band-min-hire | 1.00 | Optimal | 3,829,866 | 4,671,197 | 765/2493 | 3→14→26 | -11,918 |
