export const SHOWCASE_PATH = "/features";

export function isShowcasePath(pathname: string): boolean {
  return pathname.replace(/\/+$/, "") === SHOWCASE_PATH;
}
