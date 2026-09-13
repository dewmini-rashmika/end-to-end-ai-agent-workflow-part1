import { Sun, Sunset, Moon, CalendarDays, StickyNote } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import type { ItineraryDay as ItineraryDayType } from "@/types";

interface ItineraryDayProps {
  day: ItineraryDayType;
  className?: string;
}

interface TimeSlotProps {
  icon: React.ReactNode;
  label: string;
  content: string;
  iconBg: string;
}

function TimeSlot({ icon, label, content, iconBg }: TimeSlotProps) {
  return (
    <div className="flex gap-3">
      <div
        className={cn(
          "flex h-7 w-7 shrink-0 items-center justify-center rounded-lg mt-0.5",
          iconBg
        )}
      >
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-1">
          {label}
        </p>
        <p className="text-sm leading-relaxed text-foreground/90">{content}</p>
      </div>
    </div>
  );
}

export function ItineraryDay({ day, className }: ItineraryDayProps) {
  // Fallback to raw_text only
  if (!day.morning && !day.afternoon && !day.evening && day.raw_text) {
    return (
      <Card className={className}>
        <CardContent className="p-4">
          <p className="text-sm text-muted-foreground whitespace-pre-wrap leading-relaxed">
            {day.raw_text}
          </p>
        </CardContent>
      </Card>
    );
  }

  const slots = [
    {
      key: "morning",
      content: day.morning,
      icon: <Sun className="h-3.5 w-3.5 text-amber-600" />,
      label: "Morning",
      iconBg: "bg-amber-50",
    },
    {
      key: "afternoon",
      content: day.afternoon,
      icon: <Sunset className="h-3.5 w-3.5 text-orange-600" />,
      label: "Afternoon",
      iconBg: "bg-orange-50",
    },
    {
      key: "evening",
      content: day.evening,
      icon: <Moon className="h-3.5 w-3.5 text-indigo-600" />,
      label: "Evening",
      iconBg: "bg-indigo-50",
    },
  ].filter((s) => Boolean(s.content));

  return (
    <Card className={cn("overflow-hidden", className)}>
      <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50 pb-3 pt-4 px-4">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-blue-600 text-white text-xs font-bold shrink-0">
            {day.day ?? "?"}
          </div>
          <div>
            <CardTitle className="text-sm font-semibold">
              Day {day.day ?? ""}
              {day.date && (
                <span className="ml-2 text-xs font-normal text-muted-foreground">
                  {day.date}
                </span>
              )}
            </CardTitle>
          </div>
          <CalendarDays className="ml-auto h-4 w-4 text-muted-foreground" />
        </div>
      </CardHeader>

      <CardContent className="px-4 py-4">
        {slots.length > 0 ? (
          <div className="space-y-4">
            {slots.map((slot, i) => (
              <div key={slot.key}>
                <TimeSlot
                  icon={slot.icon}
                  label={slot.label}
                  content={slot.content!}
                  iconBg={slot.iconBg}
                />
                {i < slots.length - 1 && <Separator className="mt-4" />}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground italic">
            No activities planned.
          </p>
        )}

        {day.notes && (
          <>
            <Separator className="my-4" />
            <div className="flex gap-2 text-xs text-muted-foreground">
              <StickyNote className="h-3.5 w-3.5 shrink-0 mt-0.5" />
              <p>{day.notes}</p>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
