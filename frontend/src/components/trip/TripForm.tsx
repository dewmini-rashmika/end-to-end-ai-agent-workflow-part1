"use client";

import { useState } from "react";
import { Plane, MapPin, Calendar, ArrowRight, Loader2, Sparkles, HelpCircle } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;

    const req: PlanTripRequest = {
      user_query: query.trim(),
      ...(origin && { origin }),
      ...(destination && { destination }),
      ...(departureDate && { departure_date: departureDate }),
      ...(returnDate && { return_date: returnDate }),
      num_travelers: 1,
      trip_duration_days: 5,
      budget: "mid-range" as BudgetTier,
      interests: "",
    };

    plan(req);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      if (query.trim() && !isLoading) {
        handleSubmit(e as unknown as React.FormEvent);
      }
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-5 sm:p-6">
      {/* Header row */}
      <div className="mb-3 flex items-center gap-2">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600">
          <Sparkles className="h-4 w-4 text-white" />
        </div>
        <span className="text-sm font-semibold text-gray-800">Describe your trip</span>
        <HelpCircle className="h-4 w-4 text-gray-400 cursor-help" />
      </div>

      {/* Textarea row with inline submit button */}
      <div className="relative mb-4">
        <Textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Plan a 5-day trip from Colombo to Tokyo in October 2026 for 2 people with a mid-range budget. We love food and temples."
          className="min-h-[96px] resize-none border-0 bg-transparent p-0 pr-14 text-sm text-gray-800 placeholder:text-gray-400 focus-visible:ring-0 shadow-none"
          disabled={isLoading}
        />
        {/* Submit button — blue circle arrow */}
        <button
          type="submit"
          disabled={!query.trim() || isLoading}
          className="absolute bottom-1 right-1 flex h-10 w-10 items-center justify-center rounded-full bg-blue-600 text-white shadow-lg shadow-blue-600/40 transition-all hover:bg-blue-500 hover:scale-105 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <ArrowRight className="h-4 w-4" />
          )}
        </button>
      </div>

      {/* Divider */}
      <div className="border-t border-gray-100 mb-4" />

      {/* 4-field compact row */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {/* From */}
        <div className="space-y-1">
          <label className="flex items-center gap-1 text-xs font-medium text-gray-500">
            <Plane className="h-3 w-3" />
            From <span className="text-gray-400">(optional)</span>
          </label>
          <Input
            value={origin}
            onChange={(e) => setOrigin(e.target.value)}
            placeholder="e.g. Colombo"
            disabled={isLoading}
            className="h-9 border-gray-200 bg-gray-50 text-xs text-gray-700 placeholder:text-gray-400 focus-visible:ring-blue-500/30 focus-visible:border-blue-400"
          />
        </div>

        {/* To */}
        <div className="space-y-1">
          <label className="flex items-center gap-1 text-xs font-medium text-gray-500">
            <MapPin className="h-3 w-3" />
            To <span className="text-gray-400">(optional)</span>
          </label>
          <Input
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
            placeholder="e.g. Tokyo"
            disabled={isLoading}
            className="h-9 border-gray-200 bg-gray-50 text-xs text-gray-700 placeholder:text-gray-400 focus-visible:ring-blue-500/30 focus-visible:border-blue-400"
          />
        </div>

        {/* Departure */}
        <div className="space-y-1">
          <label className="flex items-center gap-1 text-xs font-medium text-gray-500">
            <Calendar className="h-3 w-3" />
            Departure
          </label>
          <Input
            type="date"
            value={departureDate}
            onChange={(e) => setDepartureDate(e.target.value)}
            disabled={isLoading}
            className="h-9 border-gray-200 bg-gray-50 text-xs text-gray-700 placeholder:text-gray-400 focus-visible:ring-blue-500/30 focus-visible:border-blue-400 [color-scheme:light]"
          />
        </div>

        {/* Return */}
        <div className="space-y-1">
          <label className="flex items-center gap-1 text-xs font-medium text-gray-500">
            <Calendar className="h-3 w-3" />
            Return
          </label>
          <Input
            type="date"
            value={returnDate}
            onChange={(e) => setReturnDate(e.target.value)}
            disabled={isLoading}
            className="h-9 border-gray-200 bg-gray-50 text-xs text-gray-700 placeholder:text-gray-400 focus-visible:ring-blue-500/30 focus-visible:border-blue-400 [color-scheme:light]"
          />
        </div>
      </div>

      {isLoading && (
        <p className="mt-3 text-center text-xs text-gray-400">
          Planning your trip… this takes about 30–60 seconds ✨
        </p>
      )}
    </form>
  );
}
