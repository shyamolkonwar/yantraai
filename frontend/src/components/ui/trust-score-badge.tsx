import { useState } from "react"
import { Info } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { cn, getTrustScoreColor, getTrustScoreLabel } from "@/lib/utils"

interface TrustScoreBadgeProps {
  score: number
  size?: "sm" | "md" | "lg"
  showTooltip?: boolean
  className?: string
}

export function TrustScoreBadge({
  score,
  size = "md",
  showTooltip = true,
  className
}: TrustScoreBadgeProps) {
  const [isTooltipOpen, setIsTooltipOpen] = useState(false)
  const color = getTrustScoreColor(score)
  const label = getTrustScoreLabel(score)

  const sizeClasses = {
    sm: "px-2 py-1 text-xs",
    md: "px-3 py-1.5 text-sm",
    lg: "px-4 py-2 text-base",
  }

  const colorClasses = {
    high: "bg-success/10 text-success border-success/20",
    medium: "bg-warning/10 text-warning border-warning/20",
    low: "bg-danger/10 text-danger border-danger/20",
  }

  const dotColors = {
    high: "bg-success",
    medium: "bg-warning",
    low: "bg-danger",
  }

  return (
    <div className={cn("relative inline-flex items-center", className)}>
      <motion.button
        className={cn(
          "inline-flex items-center gap-2 rounded-full border font-mono font-medium transition-all duration-200",
          sizeClasses[size],
          colorClasses[color],
          isTooltipOpen && "ring-2 ring-offset-2"
        )}
        onMouseEnter={() => showTooltip && setIsTooltipOpen(true)}
        onMouseLeave={() => setIsTooltipOpen(false)}
        onClick={() => showTooltip && setIsTooltipOpen(!isTooltipOpen)}
        aria-label={`Trust score: ${score.toFixed(2)} - ${label}`}
      >
        <div className={cn("w-2 h-2 rounded-full", dotColors[color])} />
        <span className="font-mono">{score.toFixed(2)}</span>
        {size !== 'sm' && <span className="font-sans">{label}</span>}
        {showTooltip && (
          <Info className="w-3 h-3 opacity-60" />
        )}
      </motion.button>

      <AnimatePresence>
        {isTooltipOpen && showTooltip && (
          <motion.div
            initial={{ opacity: 0, y: 8, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.95 }}
            transition={{ duration: 0.16, ease: "easeOut" }}
            className={cn(
              "absolute bottom-full left-1/2 z-50 mb-2 w-64 -translate-x-1/2",
              "rounded-lg bg-white p-3 shadow-soft border border-gray-200",
              "text-xs leading-relaxed"
            )}
          >
            <div className="font-medium text-gray-900 mb-2">
              Trust Score: {score.toFixed(2)}
            </div>
            <div className="space-y-1 text-gray-600">
              <div>Overall confidence level</div>
              <div className="space-y-0.5">
                <div className="flex justify-between">
                  <span>Status:</span>
                  <span className={cn(
                    "font-medium",
                    color === 'high' && "text-success",
                    color === 'medium' && "text-warning",
                    color === 'low' && "text-danger"
                  )}>
                    {label}
                  </span>
                </div>
                {score < 0.6 && (
                  <div className="pt-1 border-t border-gray-200">
                    <div className="text-amber-600">
                      ⚠️ Needs human review
                    </div>
                  </div>
                )}
              </div>
            </div>
            <div className="absolute bottom-0 left-1/2 w-2 h-2 -translate-x-1/2 translate-y-full rotate-45 bg-white border-r border-b border-gray-200"></div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
