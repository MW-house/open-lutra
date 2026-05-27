/** Resize handle: styled wrapper around react-resizable-panels' Separator. */
import { Separator } from "react-resizable-panels";

/** Horizontal resize handle (between left/right panels). */
export function ResizeHandleH() {
  return <Separator className="w-1 bg-border hover:bg-ring transition-colors data-resize-handle-active:bg-ring" />;
}

/** Vertical resize handle (between top/bottom panels). */
export function ResizeHandleV() {
  return <Separator className="h-1 bg-border hover:bg-ring transition-colors data-resize-handle-active:bg-ring" />;
}
