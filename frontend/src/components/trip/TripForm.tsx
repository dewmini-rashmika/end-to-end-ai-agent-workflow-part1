"use client";

import { useState } from "react";
import { Plane, MapPin, Calendar, Users, DollarSign, Search, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useTripPlanner } from "@/hooks/use-trip-planner";
import type { BudgetTier, PlanTripRequest } from "@/types";

export function TripForm() {
  const { plan, status } = useTripPlanner();
  const isLoading = status === "connecting" || status === "planning";

  const [query, setQuery] = useState("");
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [departureDate, setDepartureDate] = useState("");
  const [returnDate, setReturnDate] = useState("");
  const [numTravelers, setNumTravelers] = useState(1);
  const [tripDays, setTripDays] = useState(5);
  const [budget, setBudget] = useState<BudgetTier>("mid-range");
  const [interests, setInterests] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;

    const req: PlanTripRequest = {
      user_query: query.trim(),
      ...(origin && { origin }),
      ...(destination && { destination }),
      ...(departureDate && { departure_date: departureDate }),
      ...(returnDate && { return_date: returnDate }),
      num_travelers: numTravelers,
      trip_duration_days: tripDays,
      budget,
      interests,
    };

    plan(req);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Natural language query — primary input */}
      <div className="space-y-2">
        <Label htmlFor="query" className="text-white text-sm font-medium">
          Describe your trip *
        </Label>
        <Textarea
          id="query"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Plan a 7-day trip from London to Tokyo in November 2026 for 2 people. We love Japanese food, temples, and anime culture. Mid-range budget."
          className="min-h-[100px] bg-white/10 border-white/20 text-white placeholder:text-white/40 focus-visible:ring-white/30 focus-visible:border-white/40 resize-none"
          required
          disabled={isLoading}
        />
        <p className="text-xs text-blue-200/70">
          Be as specific as you like — dates, preferences, budget, activities, all welcome.
        </p>
      </div>

      {/* Optional structured fields — collapsible row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Origin */}
        <div className="space-y-1.5">
          <Label htmlFor="origin" className="text-white/80 text-xs font-medium flex items-center gap-1">
            <MapPin className="h-3 w-3" />
            From (optional)
          </Label>
          <Input
            id="origin"
            value={origin}
            onChange={(e) => setOrigin(e.target.value)}
            placeholder="London, LHR"
            className="bg-white/10 border-white/20 text-white placeholder:text-white/30 text-sm focus-visible:ring-white/30"
            disabled={isLoading}
          />
        </div>

        {/* Destination */}
        <div className="space-y-1.5">
          <Label htmlFor="destination" className="text-white/80 text-xs font-medium flex items-center gap-1">
            <Plane className="h-3 w-3" />
            To (optional)
          </Label>
          <Input
            id="destination"
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
            placeholder="Tokyo, NRT"
            className="bg-white/10 border-white/20 text-white placeholder:text-white/30 text-sm focus-visible:ring-white/30"
            disabled={isLoading}
          />
        </div>

        {/* Departure Date */}
        <div className="space-y-1.5">
          <Label htmlFor="departure_date" className="text-white/80 text-xs font-medium flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            Departure
          </Label>
          <Input
            id="departure_date"
            type="date"
            value={departureDate}
            onChange={(e) => setDepartureDate(e.target.value)}
            className="bg-white/10 border-white/20 text-white placeholder:text-white/30 text-sm focus-visible:ring-white/30 [color-scheme:dark]"
            disabled={isLoading}
          />
        </div>

        {/* Return Date */}
        <div className="space-y-1.5">
          <Label htmlFor="return_date" className="text-white/80 text-xs font-medium flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            Return
          </Label>
          <Input
            id="return_date"
            type="date"
            value={returnDate}
            onChange={(e) => setReturnDate(e.target.value)}
            className="bg-white/10 border-white/20 text-white placeholder:text-white/30 text-sm focus-visible:ring-white/30 [color-scheme:dark]"
            disabled={isLoading}
          />
        </div>
      </div>

      {/* Second row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {/* Travelers */}
        <div className="space-y-1.5">
          <Label htmlFor="travelers" className="text-white/80 text-xs font-medium flex items-center gap-1">
            <Users className="h-3 w-3" />
            Travelers
          </Label>
          <Input
            id="travelers"
            type="number"
            min={1}
            max={20}
            value={numTravelers}
            onChange={(e) => setNumTravelers(Number(e.target.value))}
            className="bg-white/10 border-white/20 text-white text-sm focus-visible:ring-white/30"
            disabled={isLoading}
          />
        </div>

        {/* Duration */}
        <div className="space-y-1.5">
          <Label htmlFor="duration" className="text-white/80 text-xs font-medium flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            Duration (days)
          </Label>
          <Input
            id="duration"
            type="number"
            min={1}
            max={30}
            value={tripDays}
            onChange={(e) => setTripDays(Number(e.target.value))}
            className="bg-white/10 border-white/20 text-white text-sm focus-visible:ring-white/30"
            disabled={isLoading}
          />
        </div>

        {/* Budget */}
        <div className="space-y-1.5">
          <Label className="text-white/80 text-xs font-medium flex items-center gap-1">
            <DollarSign className="h-3 w-3" />
            Budget
          </Label>
          <Select
            value={budget}
            onValueChange={(v) => setBudget(v as BudgetTier)}
            disabled={isLoading}
          >
            <SelectTrigger className="bg-white/10 border-white/20 text-white text-sm focus:ring-white/30">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="budget">🪙 Budget</SelectItem>
              <SelectItem value="mid-range">💳 Mid-range</SelectItem>
              <SelectItem value="luxury">💎 Luxury</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Interests */}
      <div className="space-y-1.5">
        <Label htmlFor="interests" className="text-white/80 text-xs font-medium">
          Interests / activities
        </Label>
        <Input
          id="interests"
          value={interests}
          onChange={(e) => setInterests(e.target.value)}
          placeholder="e.g. food, temples, hiking, art museums, nightlife"
          className="bg-white/10 border-white/20 text-white placeholder:text-white/30 text-sm focus-visible:ring-white/30"
          disabled={isLoading}
        />
      </div>

      {/* Submit */}
      <Button
        type="submit"
        size="lg"
        disabled={!query.trim() || isLoading}
        className="w-full bg-white text-blue-900 hover:bg-blue-50 font-semibold text-base h-12 transition-all"
      >
        {isLoading ? (
          <>
            <Loader2 className="mr-2 h-5 w-5 animate-spin" />
            Planning your trip…
          </>
        ) : (
          <>
            <Search className="mr-2 h-5 w-5" />
            Plan My Trip
          </>
        )}
      </Button>
    </form>
  );
}
