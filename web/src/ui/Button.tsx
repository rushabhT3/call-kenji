import type { ButtonHTMLAttributes, ReactNode } from "react";
import { Icon, type IconName } from "./Icon.tsx";

type Variant = "primary" | "secondary" | "quiet" | "danger";
type Size = "lg" | "md" | "sm";

interface ButtonProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, "className"> {
  variant?: Variant;
  size?: Size;
  icon?: IconName;
  isBusy?: boolean;
  isWide?: boolean;
  children: ReactNode;
}

export function Button({
  variant = "secondary",
  size = "md",
  icon,
  isBusy = false,
  isWide = false,
  children,
  type = "button",
  ...rest
}: ButtonProps) {
  const classes = ["button", `button--${variant}`, `button--${size}`, isWide ? "button--wide" : ""];
  return (
    <button {...rest} type={type} className={classes.join(" ").trim()} aria-busy={isBusy}>
      {icon ? <Icon name={icon} /> : null}
      <span>{children}</span>
    </button>
  );
}
