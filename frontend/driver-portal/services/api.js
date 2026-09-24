import axios from "axios";
import { mockZones, mockReservations } from "../data/mockData";

// --------------------------------------------------------------------------
// Aswan SmartCurbs AI — API layer
//
// Talks to the real FastAPI backend by default. Every function here maps
// 1:1 onto an endpoint documented in backend/app/api/v1/*.py, and converts
// the backend's snake_case payloads into the camelCase shape the Driver
// Portal's pages use, so no component needs to know about the wire format.
//
// Set VITE_USE_MOCK_DATA=true in a .env file to fall back to in-memory mock
// data (useful for a presentation if the backend / database isn't running).
// --------------------------------------------------------------------------

const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === "true";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8001/api/v1";

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 8000,
  headers: {
    "Content-Type": "application/json",
  },
});

const MOCK_LATENCY_MS = 400;

function delay(value, ms = MOCK_LATENCY_MS) {
  return new Promise((resolve) => setTimeout(() => resolve(structuredClone(value)), ms));
}

function notFound(message) {
  const error = new Error(message);
  error.status = 404;
  return error;
}

// --------------------------------------------------------------------------
// Normalization helpers — backend snake_case -> frontend camelCase
// --------------------------------------------------------------------------

function normalizeZone(zone) {
  // From GET /zones or GET /zones/{id} (ZoneResponse)
  return {
    id: zone.id,
    name: zone.name,
    address: zone.location,
    capacity: zone.total_spaces,
    latitude: zone.latitude,
    longitude: zone.longitude,
    type: (zone.zone_type || "PAID").toUpperCase(),
    hourlyRate: zone.hourly_rate ?? null,
    operatingHours: zone.operating_hours || null,
    rules: zone.rules || null,
    restrictionReason: zone.restriction_reason || null,
    createdAt: zone.created_at,
  };
}

function normalizeAvailabilitySummary(summary) {
  // From GET /availability (ZoneAvailabilitySummary)
  return {
    id: summary.zone_id,
    name: summary.zone_name,
    address: summary.location,
    capacity: summary.total_spaces,
    available: summary.available_count,
    occupied: summary.occupied_count + summary.reserved_count,
    reserved: summary.reserved_count,
    type: (summary.zone_type || "PAID").toUpperCase(),
    hourlyRate: summary.hourly_rate ?? null,
    operatingHours: summary.operating_hours || null,
    rules: summary.rules || null,
    restrictionReason: summary.restriction_reason || null,
  };
}

function normalizeAvailabilityDetail(detail) {
  // From GET /availability/{zone_id} (ZoneAvailabilityResponse)
  const capacity = detail.total_spaces;
  const occupancyPercent = capacity > 0
    ? Math.round(((detail.occupied_count + detail.reserved_count) / capacity) * 100)
    : 0;

  return {
    zoneId: detail.zone_id,
    name: detail.zone_name,
    address: detail.location,
    capacity,
    available: detail.available_count,
    occupied: detail.occupied_count + detail.reserved_count,
    reserved: detail.reserved_count,
    occupancyPercent,
    type: (detail.zone_type || "PAID").toUpperCase(),
    hourlyRate: detail.hourly_rate ?? null,
    operatingHours: detail.operating_hours || null,
    rules: detail.rules || null,
    restrictionReason: detail.restriction_reason || null,
    spaces: detail.spaces.map((space) => ({
      id: space.id,
      number: space.space_number,
      status: space.status, // "available" | "occupied" | "reserved"
    })),
  };
}

function normalizeReservation(reservation) {
  // From POST/GET /reservations... (ReservationResponse)
  return {
    id: reservation.id,
    spaceId: reservation.space_id,
    driverName: reservation.driver_name,
    driverEmail: reservation.driver_email,
    driverPhone: reservation.driver_phone,
    plateNumber: reservation.vehicle_plate,
    vehicleModel: reservation.vehicle_model || "Car — Sedan",
    status: reservation.status,
    startTime: reservation.start_time,
    endTime: reservation.end_time,
    createdAt: reservation.created_at,
  };
}

// --------------------------------------------------------------------------
// Mock helpers (only used when USE_MOCK_DATA is true)
// --------------------------------------------------------------------------

function mockZoneById(id) {
  return mockZones.find((zone) => zone.id === Number(id)) || null;
}

function mockAvailabilitySummary(zone) {
  const available = zone.spaces.filter((s) => s.status === "available").length;
  const occupied = zone.spaces.filter((s) => s.status === "occupied").length;
  const reserved = zone.spaces.filter((s) => s.status === "reserved").length;
  return {
    zone_id: zone.id,
    zone_name: zone.name,
    location: zone.location,
    total_spaces: zone.total_spaces,
    available_count: available,
    occupied_count: occupied,
    reserved_count: reserved,
  };
}

// --------------------------------------------------------------------------
// Public API — used by pages/components
// --------------------------------------------------------------------------

/**
 * Fetch all parking zones with live availability counts.
 * Backend: GET /api/v1/availability
 */
export async function getParkingZones() {
  if (USE_MOCK_DATA) {
    const summaries = mockZones.map(mockAvailabilitySummary);
    return delay(summaries.map(normalizeAvailabilitySummary));
  }
  const { data } = await apiClient.get("/availability");
  return data.map(normalizeAvailabilitySummary);
}

/**
 * Fetch static metadata for a single zone (name, address, capacity, coords).
 * Backend: GET /api/v1/zones/{id}
 */
export async function getParkingZoneById(id) {
  if (USE_MOCK_DATA) {
    const zone = mockZoneById(id);
    if (!zone) throw notFound(`Parking zone "${id}" was not found.`);
    return delay(normalizeZone(zone));
  }
  const { data } = await apiClient.get(`/zones/${id}`);
  return normalizeZone(data);
}

/**
 * Fetch live availability + the full list of spaces (with status) for one zone.
 * Backend: GET /api/v1/availability/{zone_id}
 */
export async function getParkingAvailability(id) {
  if (USE_MOCK_DATA) {
    const zone = mockZoneById(id);
    if (!zone) throw notFound(`Parking zone "${id}" was not found.`);
    const summary = mockAvailabilitySummary(zone);
    return delay(
      normalizeAvailabilityDetail({
        ...summary,
        spaces: zone.spaces.map((s) => ({ id: s.id, space_number: s.space_number, status: s.status })),
      })
    );
  }
  const { data } = await apiClient.get(`/availability/${id}`);
  return normalizeAvailabilityDetail(data);
}

/**
 * Create a reservation for one specific parking space.
 * Expected payload: { spaceId, driverName, driverEmail, driverPhone, plateNumber, vehicleModel }
 * Backend: POST /api/v1/reservations
 */
export async function createReservation({
  spaceId,
  driverName,
  driverEmail,
  driverPhone,
  plateNumber,
  vehicleModel,
  startTime,
  endTime,
  durationMinutes,
}) {
  if (USE_MOCK_DATA) {
    const zone = mockZones.find((z) => z.spaces.some((s) => s.id === Number(spaceId)));
    const space = zone?.spaces.find((s) => s.id === Number(spaceId));
    if (!zone || !space) throw notFound(`Parking space "${spaceId}" was not found.`);
    if (space.status !== "available") {
      const error = new Error(`Space ${space.space_number} is currently '${space.status}' and cannot be reserved.`);
      error.status = 400;
      throw error;
    }
    space.status = "reserved";
    const reservation = {
      id: mockReservations.length + 1,
      space_id: space.id,
      driver_name: driverName,
      driver_email: driverEmail,
      driver_phone: driverPhone,
      vehicle_plate: plateNumber,
      vehicle_model: vehicleModel || "Car — Sedan",
      status: "active",
      start_time: startTime || new Date().toISOString(),
      end_time: endTime || null,
      created_at: new Date().toISOString(),
    };
    mockReservations.push(reservation);
    return delay(normalizeReservation(reservation));
  }

  const { data } = await apiClient.post("/reservations", {
    space_id: Number(spaceId),
    driver_name: driverName,
    driver_email: driverEmail,
    driver_phone: driverPhone,
    vehicle_plate: plateNumber,
    vehicle_model: vehicleModel || "Car — Sedan",
    start_time: startTime || null,
    end_time: endTime || null,
    duration_minutes: durationMinutes || null,
  });
  return normalizeReservation(data);
}

/**
 * Fetch a single reservation by ID.
 * Backend: GET /api/v1/reservations/{id}
 */
export async function getReservation(id) {
  const { data } = await apiClient.get(`/reservations/${id}`);
  return normalizeReservation(data);
}

