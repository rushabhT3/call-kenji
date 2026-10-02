import type { ButtonHTMLAttributes, ReactNode } from "react";
import { buttonClassName, type ButtonSize, type ButtonVariant } from "./buttonClassName.ts";
import { Icon, type IconName } from "./Icon.tsx";

interface ButtonProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, "className"> {
  variant?: ButtonVariant;
  size?: ButtonSize;
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
  return (
    <button
      {...rest}
      type={type}
      className={buttonClassName(variant, size, isWide)}
      aria-busy={isBusy}
    >
      {icon ? <Icon name={icon} /> : null}
      <span>{children}</span>
    </button>
  );
}
