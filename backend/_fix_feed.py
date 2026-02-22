"""Replace feed cards section in Businesses.tsx with real business data rendering."""
import re

path = r"C:\Users\nadee\OneDrive\Documents\GitHub\Vantage\frontend\src\pages\Businesses.tsx"
with open(path, "r", encoding="utf-8", errors="replace") as f:
    content = f.read()

# Find the section: from "{feedCards.map((cardId)" to the closing "})}"\n before "Infinite scroll sentinel"
# We use a regex that matches from the feedCards.map block through the closing })}
pattern = r'(\{feedCards\.map\(\(cardId\).*?\n\s*\}\)\})'
match = re.search(pattern, content, re.DOTALL)
if not match:
    print("ERROR: Could not find feedCards.map block")
    exit(1)

print(f"Found feedCards.map block at positions {match.start()}-{match.end()}")

new_block = """{feedCards.map((cardId) => {
                  const liked = feedLiked.has(cardId);
                  const saved = feedSaved.has(cardId);
                  const biz = filtered[cardId];

                  return (
                    <div
                      key={cardId}
                      className="glass-card rounded-2xl overflow-hidden animate-fade-in group"
                    >
                      {/* Header */}
                      <div className="flex items-center gap-3 px-5 py-4">
                        {biz?.image_url ? (
                          <img src={biz.image_url} alt="" className="w-10 h-10 rounded-full object-cover flex-shrink-0" />
                        ) : (
                          <div className="w-10 h-10 rounded-full bg-[hsl(var(--muted))] flex-shrink-0" />
                        )}
                        <div className="min-w-0 flex-1">
                          {biz ? (
                            <>
                              <p className="text-sm font-semibold text-[hsl(var(--foreground))] truncate">{biz.name}</p>
                              <p className="text-xs text-[hsl(var(--muted-foreground))] truncate capitalize">{biz.category} · {biz.address || 'Local Business'}</p>
                            </>
                          ) : (
                            <div className="space-y-1.5">
                              <div className="h-3.5 w-32 rounded-full skeleton" />
                              <div className="h-2.5 w-48 rounded-full skeleton" />
                            </div>
                          )}
                        </div>
                        {biz && biz.rating > 0 && (
                          <span className="flex items-center gap-1 text-xs font-medium text-amber-600 dark:text-amber-400 flex-shrink-0">
                            <Star className="w-3.5 h-3.5 fill-current" />
                            {biz.rating.toFixed(1)}
                          </span>
                        )}
                      </div>

                      {/* Image area */}
                      <div
                        className="relative aspect-[4/3] overflow-hidden bg-[hsl(var(--muted))] cursor-pointer"
                        onClick={() => biz && setSelectedBusiness(biz)}
                      >
                        {biz?.image_url ? (
                          <img src={biz.image_url} alt={biz.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
                        ) : (
                          <div className="absolute inset-0 bg-gradient-to-br from-brand-light/20 via-brand/10 to-brand-dark/10 animate-gradient" />
                        )}
                        {biz?.has_deals && (
                          <div className="absolute top-4 right-4">
                            <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold text-white bg-brand shadow-lg shadow-brand/25">
                              <Tag className="w-3 h-3" />
                              Deal
                            </span>
                          </div>
                        )}
                        {biz && biz.review_count > 0 && (
                          <div className="absolute bottom-4 left-4 flex items-center gap-1 px-2.5 py-1 rounded-full bg-black/40 backdrop-blur-sm text-white text-xs font-medium">
                            <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
                            {biz.rating.toFixed(1)} &middot; {biz.review_count} reviews
                          </div>
                        )}
                      </div>

                      {/* Social actions bar */}
                      <div className="px-5 py-3 flex items-center justify-between border-b border-[hsl(var(--border))]">
                        <div className="flex items-center gap-4">
                          <button
                            onClick={() => setFeedLiked(prev => {
                              const next = new Set(prev);
                              next.has(cardId) ? next.delete(cardId) : next.add(cardId);
                              return next;
                            })}
                            className="flex items-center gap-1.5 group/btn"
                          >
                            <Heart className={cn('w-5 h-5 transition-transform duration-200', liked ? 'text-red-500 fill-red-500 scale-110' : 'text-[hsl(var(--muted-foreground))] group-hover/btn:text-red-400')} />
                            <span className={cn('text-xs font-medium', liked ? 'text-red-500' : 'text-[hsl(var(--muted-foreground))]')}>
                              {liked ? 'Liked' : 'Like'}
                            </span>
                          </button>
                          <button className="flex items-center gap-1.5 text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--primary))] transition-colors">
                            <MessageCircle className="w-5 h-5" />
                            <span className="text-xs font-medium">Comment</span>
                          </button>
                          <button className="flex items-center gap-1.5 text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--primary))] transition-colors">
                            <Share2 className="w-5 h-5" />
                            <span className="text-xs font-medium">Share</span>
                          </button>
                        </div>
                        <button
                          onClick={() => setFeedSaved(prev => {
                            const next = new Set(prev);
                            next.has(cardId) ? next.delete(cardId) : next.add(cardId);
                            return next;
                          })}
                        >
                          <Bookmark className={cn('w-5 h-5 transition-colors', saved ? 'text-[hsl(var(--primary))] fill-[hsl(var(--primary))]' : 'text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--primary))]')} />
                        </button>
                      </div>

                      {/* Description */}
                      <div className="px-5 py-4">
                        {biz ? (
                          <p className="text-sm text-[hsl(var(--muted-foreground))] line-clamp-2">{biz.description || 'A local business near you.'}</p>
                        ) : (
                          <div className="space-y-2">
                            <div className="h-3.5 w-3/4 rounded-full skeleton" />
                            <div className="h-3 w-full rounded-full skeleton" />
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}"""

content = content[:match.start()] + new_block + content[match.end():]

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("OK - Feed cards replaced with real business data rendering")
