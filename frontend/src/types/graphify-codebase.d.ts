declare module "graphify-codebase/viewer" {
  export function renderGraph(
    element: HTMLElement,
    data: unknown,
    options?: Record<string, unknown>
  ): void;
}
