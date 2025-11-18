"use client"

import { Toaster as Sonner } from "sonner"

const Toaster = () => {
  return (
    <Sonner
      position="top-right"
      expand={false}
      richColors
      closeButton
    />
  )
}

export { Toaster }