"use client"

import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { cn } from "@/lib/utils"
import { Button } from "./button"

export interface DialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title?: string
  description?: string
  children?: React.ReactNode
  confirmText?: string
  cancelText?: string
  onConfirm?: () => void
  onCancel?: () => void
  variant?: "default" | "destructive"
}

const Dialog = ({
  open,
  onOpenChange,
  title,
  description,
  children,
  confirmText = "Confirm",
  cancelText = "Cancel",
  onConfirm,
  onCancel,
  variant = "default",
}: DialogProps) => {
  const handleCancel = () => {
    onCancel?.()
    onOpenChange(false)
  }

  const handleConfirm = () => {
    onConfirm?.()
    onOpenChange(false)
  }

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-50 bg-black/50"
            onClick={handleCancel}
          />
          
          {/* Dialog */}
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ duration: 0.2 }}
              className={cn(
                "relative w-full max-w-lg rounded-lg border bg-background p-6 shadow-lg",
                "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              )}
              onClick={(e) => e.stopPropagation()}
            >
              {title && (
                <h2 className="text-lg font-semibold mb-2">{title}</h2>
              )}
              {description && (
                <p className="text-sm text-muted-foreground mb-4">{description}</p>
              )}
              {children}
              <div className="flex justify-end gap-2 mt-6">
                <Button variant="outline" onClick={handleCancel}>
                  {cancelText}
                </Button>
                <Button
                  variant={variant === "destructive" ? "destructive" : "default"}
                  onClick={handleConfirm}
                >
                  {confirmText}
                </Button>
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  )
}

export { Dialog }

