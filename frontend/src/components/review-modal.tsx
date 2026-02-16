"use client"

import { useState } from "react"
import { Star, Send, Loader2, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { api } from "@/api"
import { useAuth } from "@/contexts/AuthContext"

interface ReviewModalProps {
  businessId: string
  businessName: string
  isOpen: boolean
  onClose: () => void
  onReviewAdded?: () => void
}

export function ReviewModal({ businessId, businessName, isOpen, onClose, onReviewAdded }: ReviewModalProps) {
  const { isAuthenticated } = useAuth()
  const [rating, setRating] = useState(5)
  const [hoveredRating, setHoveredRating] = useState(0)
  const [comment, setComment] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState("")

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!isAuthenticated) {
      setError("Please sign in to submit a review")
      return
    }
    if (comment.length < 5) {
      setError("Review must be at least 5 characters")
      return
    }

    setSubmitting(true)
    setError("")
    try {
      await api.createReview({ business_id: businessId, rating, comment })
      setRating(5)
      setComment("")
      onReviewAdded?.()
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit review")
    } finally {
      setSubmitting(false)
    }
  }

  const ratingLabels = ['', 'Poor', 'Fair', 'Good', 'Very Good', 'Excellent']

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fade-in" onClick={onClose}>
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
      <div
        className="relative w-full max-w-md rounded-2xl bg-[hsl(var(--card))] border border-[hsl(var(--border))] shadow-2xl p-6 animate-scale-in"
        onClick={(e) => e.stopPropagation()}
      >
        <button onClick={onClose} className="absolute top-4 right-4 w-8 h-8 rounded-full hover:bg-[hsl(var(--secondary))] flex items-center justify-center transition-colors">
          <X className="w-4 h-4 text-[hsl(var(--muted-foreground))]" />
        </button>

        <h3 className="text-lg font-bold text-[hsl(var(--foreground))] mb-1">Review {businessName}</h3>
        <p className="text-sm text-[hsl(var(--muted-foreground))] mb-5">Share your experience</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Rating */}
          <div>
            <label className="text-sm font-medium text-[hsl(var(--foreground))] mb-2 block">Your Rating</label>
            <div className="flex items-center gap-1">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  type="button"
                  onClick={() => setRating(star)}
                  onMouseEnter={() => setHoveredRating(star)}
                  onMouseLeave={() => setHoveredRating(0)}
                  className="p-0.5"
                >
                  <Star
                    className={cn(
                      "w-8 h-8 transition-colors",
                      star <= (hoveredRating || rating) ? "text-amber-400 fill-amber-400" : "text-[hsl(var(--border))]"
                    )}
                  />
                </button>
              ))}
              <span className="ml-2 text-sm text-[hsl(var(--muted-foreground))]">{ratingLabels[hoveredRating || rating]}</span>
            </div>
          </div>

          {/* Comment */}
          <div>
            <label className="text-sm font-medium text-[hsl(var(--foreground))] mb-2 block">Your Review</label>
            <textarea
              placeholder="Tell others about your experience..."
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              rows={4}
              className="w-full rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--background))] px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[hsl(var(--primary))]/20 focus:border-[hsl(var(--primary))] resize-none"
              required
            />
          </div>

          {error && <p className="text-sm text-red-500">{error}</p>}

          <div className="flex gap-2 justify-end pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2.5 rounded-xl text-sm font-medium text-[hsl(var(--muted-foreground))] hover:bg-[hsl(var(--secondary))] transition-colors">
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || comment.length < 5}
              className="px-5 py-2.5 rounded-xl text-sm font-medium gradient-primary text-white disabled:opacity-50 flex items-center gap-2"
            >
              {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              Submit Review
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
