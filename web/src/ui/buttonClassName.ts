export type ButtonVariant = "primary" | "secondary" | "quiet" | "danger";
export type ButtonSize = "lg" | "md" | "sm";

export function buttonClassName(variant: ButtonVariant, size: ButtonSize, isWide = false): string {
  const classes = ["button", `button--${variant}`, `button--${size}`, isWide ? "button--wide" : ""];
  return classes.join(" ").trim();
}
