import { Building2, Star, MapPin, ExternalLink, Wifi } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { formatRating, formatPriceLevel } from "@/lib/utils";
import type { HotelResult } from "@/types";

interface HotelCardProps {
  hotel: HotelResult;
  className?: string;
}

const TIER_BADGE: Record<
  string,
  { label: string; variant: "default" | "secondary" | "outline" }
> = {
  budget: { label: "🪙 Budget", variant: "secondary" },
  "mid-range": { label: "💳 Mid-range", variant: "default" },
  luxury: { label: "💎 Luxury", variant: "default" },
};

export function HotelCard({ hotel, className }: HotelCardProps) {
  // Fallback to raw_text only
  if (!hotel.name && !hotel.address && hotel.raw_text) {
    return (
      <Card className={className}>
        <CardContent className="p-4">
          <p className="text-sm text-muted-foreground whitespace-pre-wrap leading-relaxed">
            {hotel.raw_text}
          </p>
        </CardContent>
      </Card>
    );
  }

  const tierInfo = hotel.tier ? TIER_BADGE[hotel.tier] : null;

  return (
    <Card className={className}>
      <CardHeader className="pb-3 pt-4 px-4">
        <div className="flex items-start justify-between gap-2">
          {/* Name + address */}
          <div className="flex items-start gap-2 min-w-0">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-amber-50 mt-0.5">
              <Building2 className="h-4 w-4 text-amber-600" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold leading-tight truncate">
                {hotel.name ?? "Hotel"}
              </p>
              {hotel.address && (
                <p className="text-xs text-muted-foreground mt-0.5 flex items-start gap-1">
                  <MapPin className="h-3 w-3 shrink-0 mt-0.5" />
                  <span className="truncate">{hotel.address}</span>
                </p>
              )}
            </div>
          </div>

          {/* Tier badge */}
          {tierInfo && (
            <Badge variant={tierInfo.variant} className="shrink-0 text-xs">
              {tierInfo.label}
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="px-4 pb-4 space-y-3">
        {/* Rating + price */}
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            {hotel.rating != null && (
              <span className="flex items-center gap-1 text-sm font-medium">
                <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
                {formatRating(hotel.rating)}
                {hotel.total_ratings ? (
                  <span className="text-xs text-muted-foreground font-normal">
                    ({hotel.total_ratings.toLocaleString()})
                  </span>
                ) : null}
              </span>
            )}
            {hotel.price_level != null && (
              <span className="text-sm text-muted-foreground">
                {formatPriceLevel(hotel.price_level)}
              </span>
            )}
          </div>

          {hotel.price_per_night_usd != null && (
            <div className="text-right">
              <p className="text-base font-bold">
                ${hotel.price_per_night_usd.toLocaleString()}
              </p>
              <p className="text-xs text-muted-foreground">/ night</p>
            </div>
          )}
        </div>

        {/* Amenities */}
        {hotel.amenities && hotel.amenities.length > 0 && (
          <>
            <Separator />
            <div className="flex flex-wrap gap-1.5">
              {hotel.amenities.slice(0, 6).map((amenity) => (
                <Badge
                  key={amenity}
                  variant="secondary"
                  className="text-xs px-2 py-0.5"
                >
                  {amenity}
                </Badge>
              ))}
              {hotel.amenities.length > 6 && (
                <Badge variant="outline" className="text-xs px-2 py-0.5 text-muted-foreground">
                  +{hotel.amenities.length - 6} more
                </Badge>
              )}
            </div>
          </>
        )}

        {/* External link */}
        {hotel.url && (
          <>
            <Separator />
            <a
              href={hotel.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-xs text-blue-600 hover:text-blue-700 transition-colors"
            >
              <ExternalLink className="h-3 w-3" />
              View on Google Maps
            </a>
          </>
        )}
      </CardContent>
    </Card>
  );
}
