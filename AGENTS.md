# Development Rules

## CSS: Button Styling

The global `button` style in `frontend/src/assets/main.css` sets `color: #fff; background: #111`. When any scoped component style overrides `background` to a light/white color on a `<button>` element, it MUST also explicitly set `color` to a dark value (e.g. `color: #333`). Otherwise the inherited white text will be invisible on the light background.

**Rule:** Every scoped CSS rule that applies to `<button>` elements and sets a light `background` must also set `color` explicitly. Both `background` and `color` must always be set together for button overrides.
