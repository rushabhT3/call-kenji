import type { AnchorHTMLAttributes, ReactNode } from "react";
import { buttonClassName, type ButtonSize, type ButtonVariant } from "./buttonClassName.ts";
import { Icon, type IconName } from "./Icon.tsx";

interface ButtonLinkProps extends Omit<AnchorHTMLAttributes<HTMLAnchorElement>, "className"> {
  href: string;
  variant?: ButtonVariant;
  size?: ButtonSize;
  icon?: IconName;
  children: ReactNode;
}

/** A link that looks like a button, for actions that take the visitor to another page. */
export function ButtonLink({
  variant = "secondary",
  size = "md",
  icon,
  children,
  ...rest
}: ButtonLinkProps) {
  return (
    <a {...rest} className={buttonClassName(variant, size)}>
      {icon ? <Icon name={icon} /> : null}
      <span>{children}</span>
    </a>
  );
}
