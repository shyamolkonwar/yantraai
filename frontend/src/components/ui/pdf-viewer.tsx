"use client"

import { useState, useRef, useCallback } from "react"
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, Maximize2, Eye } from "lucide-react"
import { motion } from "framer-motion"
import { Button } from "./button"
import { cn } from "@/lib/utils"

interface PDFViewerProps {
  fileUrl?: string
  pageNumber: number
  onPageChange: (page: number) => void
  totalPages: number
  className?: string
  regions?: Array<{
    id: string
    bbox: { x1: number; y1: number; x2: number; y2: number }
    label: string
    trustScore: number
    piiDetected: boolean
  }>
  selectedRegionId?: string
  onRegionSelect?: (regionId: string) => void
  showRedactions?: boolean
}

export function PDFViewer({
  fileUrl,
  pageNumber,
  onPageChange,
  totalPages,
  className,
  regions = [],
  selectedRegionId,
  onRegionSelect,
  showRedactions = false
}: PDFViewerProps) {
  const [scale, setScale] = useState(1)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  const handleZoomIn = () => {
    setScale(prev => Math.min(prev + 0.25, 3))
  }

  const handleZoomOut = () => {
    setScale(prev => Math.max(prev - 0.25, 0.5))
  }

  const handleFitToWidth = () => {
    if (containerRef.current) {
      const containerWidth = containerRef.current.clientWidth - 32 // Padding
      const estimatedPageWidth = 612 // Standard PDF page width in points
      const newScale = containerWidth / estimatedPageWidth
      setScale(newScale)
    }
  }

  const handlePagePrevious = () => {
    if (pageNumber > 1) {
      onPageChange(pageNumber - 1)
    }
  }

  const handlePageNext = () => {
    if (pageNumber < totalPages) {
      onPageChange(pageNumber + 1)
    }
  }

  const handleRegionClick = useCallback((regionId: string) => {
    onRegionSelect?.(regionId)
  }, [onRegionSelect])

  const getRegionStyle = useCallback((region: any) => {
    if (!canvasRef.current) return {}

    // This would calculate the actual pixel positions based on scale
    // For now, using a simplified approach
    const { x1, y1, x2, y2 } = region.bbox
    const scaled = {
      x1: x1 * scale,
      y1: y1 * scale,
      x2: x2 * scale,
      y2: y2 * scale,
      width: (x2 - x1) * scale,
      height: (y2 - y1) * scale
    }

    return {
      left: `${scaled.x1}px`,
      top: `${scaled.y1}px`,
      width: `${scaled.width}px`,
      height: `${scaled.height}px`,
    }
  }, [scale])

  return (
    <div className={cn("bg-white rounded-lg border border-gray-200 shadow-soft", className)}>
      {/* Toolbar */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handlePagePrevious}
            disabled={pageNumber <= 1}
          >
            <ChevronLeft className="w-4 h-4" />
          </Button>

          <span className="text-sm font-medium text-gray-700 px-3">
            Page {pageNumber} of {totalPages}
          </span>

          <Button
            variant="outline"
            size="sm"
            onClick={handlePageNext}
            disabled={pageNumber >= totalPages}
          >
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleZoomOut}
            disabled={scale <= 0.5}
          >
            <ZoomOut className="w-4 h-4" />
          </Button>

          <span className="text-sm font-medium text-gray-700 w-12 text-center">
            {Math.round(scale * 100)}%
          </span>

          <Button
            variant="outline"
            size="sm"
            onClick={handleZoomIn}
            disabled={scale >= 3}
          >
            <ZoomIn className="w-4 h-4" />
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleFitToWidth}
          >
            <Maximize2 className="w-4 h-4" />
          </Button>

          <Button
            variant={showRedactions ? "default" : "outline"}
            size="sm"
            onClick={() => {}} // Will be connected to redaction toggle
          >
            <Eye className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* PDF Canvas Container */}
      <div
        ref={containerRef}
        className="relative overflow-auto"
        style={{ height: '600px' }}
      >
        <div className="flex justify-center p-4">
          {fileUrl ? (
            <div className="relative">
              {/* This would render the actual PDF - for now showing a placeholder */}
              <div
                className="bg-white border border-gray-300 shadow-lg"
                style={{
                  width: `${612 * scale}px`,
                  height: `${792 * scale}px`,
                  transform: `scale(${scale})`,
                  transformOrigin: 'top left'
                }}
              >
                <div className="w-full h-full flex items-center justify-center text-gray-400">
                  <div className="text-center">
                    <div className="text-sm mb-2">PDF Document</div>
                    <div className="text-xs">Page {pageNumber}</div>
                  </div>
                </div>
              </div>

              {/* Overlay Regions */}
              <motion.div
                className="absolute inset-0 pointer-events-none"
                style={{ transform: `scale(${scale})`, transformOrigin: 'top left' }}
              >
                {regions.map((region, index) => {
                  const isSelected = selectedRegionId === region.id
                  const hasPII = region.piiDetected

                  return (
                    <motion.div
                      key={region.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 0.6 }}
                      transition={{
                        delay: index * 0.05,
                        duration: 0.4
                      }}
                      className={cn(
                        "absolute border-2 cursor-pointer pointer-events-auto transition-all duration-200",
                        isSelected ? "border-brand-600 bg-brand-100/20" : "border-transparent hover:border-brand-400",
                        hasPII && !showRedactions && "border-danger bg-danger/10",
                        showRedactions && hasPII && "bg-gray-900/80 border-gray-800"
                      )}
                      style={getRegionStyle(region)}
                      onClick={() => handleRegionClick(region.id)}
                      whileHover={{ scale: 1.01 }}
                      whileTap={{ scale: 0.99 }}
                    >
                      {/* Trust Score Indicator */}
                      {!showRedactions && (
                        <div className={cn(
                          "absolute -top-1 -right-1 w-3 h-3 rounded-full border-2 border-white",
                          region.trustScore >= 0.8 ? "bg-success" :
                          region.trustScore >= 0.5 ? "bg-warning" : "bg-danger"
                        )} />
                      )}

                      {/* PII Indicator */}
                      {!showRedactions && hasPII && (
                        <div className="absolute -top-1 -left-1 w-3 h-3 bg-danger rounded-full border-2 border-white" />
                      )}

                      {/* Redaction Blur Effect */}
                      {showRedactions && hasPII && (
                        <div className="absolute inset-0 backdrop-blur-sm bg-gray-900/40" />
                      )}
                    </motion.div>
                  )
                })}
              </motion.div>
            </div>
          ) : (
            <div className="flex items-center justify-center" style={{ height: '600px' }}>
              <div className="text-center text-gray-400">
                <Eye className="w-12 h-12 mx-auto mb-4" />
                <p>No document to display</p>
                <p className="text-sm mt-2">Upload a document to get started</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}