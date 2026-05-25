# Legitimacy Is Infrastructure

**A pro-build operating doctrine for AI data centers**

Technical position paper by Sasan Salmanzadeh.

AI data centers are strategic infrastructure. If hyperscalers let water, grid, noise, construction, tax, land, security, cultural, and community issues collapse into one public anti-AI story, they will lose legitimacy before the buildout can mature.

The answer is not PR. The answer is proof, category discipline, redesign gates, durable local benefit, and a build philosophy that treats legitimacy as infrastructure.

## Read

- [Designed dark-mode paper](paper.html)
- [Canonical Markdown](paper.md)
- [PDF snapshot](paper.pdf)
- [Source notes](sources.md)

## Thesis

The paper argues that AI data centers should be treated less like opaque compounds and more like civic infrastructure whose legitimacy has to be designed, verified, maintained, and improved in public.

The goal is not anti-build delay. The goal is the opposite: build faster by proving more, separating categories before discourse collapses them, and over-delivering on the local systems that make frontier compute politically and operationally durable.

## Format

`paper.md` is the source of truth. `paper.html` and `paper.pdf` are generated snapshots for easier reading and sharing.

To regenerate the designed artifacts locally:

```sh
python3 tools/render_dark_paper.py --paper paper.md --html paper.html --pdf paper.pdf
```

The renderer uses only Python standard library plus local Chrome/Chromium for PDF export.
