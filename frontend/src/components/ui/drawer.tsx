import * as React from "react"
import { XIcon } from "lucide-react"
import { Dialog as DialogPrimitive } from "radix-ui"

import { cn } from "@/lib/utils"

function Drawer({ ...props }: React.ComponentProps<typeof DialogPrimitive.Root>) {
  return <DialogPrimitive.Root data-slot="drawer" {...props} />
}

function DrawerTrigger({ ...props }: React.ComponentProps<typeof DialogPrimitive.Trigger>) {
  return <DialogPrimitive.Trigger data-slot="drawer-trigger" {...props} />
}

function DrawerClose({ ...props }: React.ComponentProps<typeof DialogPrimitive.Close>) {
  return <DialogPrimitive.Close data-slot="drawer-close" {...props} />
}

function DrawerContent({
  className,
  children,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Content>) {
  return (
    <DialogPrimitive.Portal data-slot="drawer-portal">
      <DialogPrimitive.Overlay
        data-slot="drawer-overlay"
        className="fixed inset-0 z-50 bg-bg-base/80 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:animate-in data-[state=open]:fade-in-0"
      />
      <DialogPrimitive.Content
        data-slot="drawer-content"
        className={cn(
          "fixed inset-y-0 right-0 z-50 flex w-full max-w-xl flex-col border-l border-border-subtle bg-bg-elevated p-6 text-text-primary shadow-soft outline-none data-[state=closed]:animate-out data-[state=closed]:slide-out-to-right data-[state=open]:animate-in data-[state=open]:slide-in-from-right sm:rounded-l-2xl",
          className,
        )}
        {...props}
      >
        {children}
      </DialogPrimitive.Content>
    </DialogPrimitive.Portal>
  )
}

function DrawerHeader({ className, ...props }: React.ComponentProps<"div">) {
  return <div data-slot="drawer-header" className={cn("flex items-start justify-between gap-4", className)} {...props} />
}

function DrawerTitle({ className, ...props }: React.ComponentProps<typeof DialogPrimitive.Title>) {
  return <DialogPrimitive.Title data-slot="drawer-title" className={cn("text-xl font-semibold", className)} {...props} />
}

function DrawerDescription({ className, ...props }: React.ComponentProps<typeof DialogPrimitive.Description>) {
  return <DialogPrimitive.Description data-slot="drawer-description" className={cn("text-sm text-text-secondary", className)} {...props} />
}

function DrawerDismiss() {
  return (
    <DialogPrimitive.Close
      className="grid size-10 shrink-0 place-items-center rounded-xl text-text-secondary transition-colors hover:bg-bg-surface hover:text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan/60"
    >
      <XIcon />
      <span className="sr-only">關閉</span>
    </DialogPrimitive.Close>
  )
}

export {
  Drawer,
  DrawerClose,
  DrawerContent,
  DrawerDescription,
  DrawerDismiss,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger,
}
