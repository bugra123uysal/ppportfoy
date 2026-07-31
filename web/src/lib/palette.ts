/**
 * Categorical slots (dark column), validated against this app's card surface
 * (#111318): `node scripts/validate_palette.js "<hexes>" --mode dark --surface
 * "#111318"` -- all 8 checks pass. See the ECC dataviz skill for the method.
 * Fixed order, assigned in sequence, never cycled or generated past slot 8.
 */
export const CATEGORICAL_PALETTE = [
  "#3987e5", // blue
  "#d95926", // orange
  "#199e70", // aqua
  "#c98500", // yellow
  "#d55181", // magenta
  "#008300", // green -- documented value, unmodified (do not eyeball a substitute)
  "#9085e9", // violet
  "#e66767", // red
] as const;

export const OTHER_SLOT_COLOR = "#5b6272"; // text-faint -- "Diğer" bucket, deliberately neutral
