import { describe, expect, it } from "vitest";
import { formatCompactTaka, formatInt, formatPercent, formatSignedPercentPoints } from "./format";

describe("formatInt", () => {
  it("groups thousands and rounds", () => {
    expect(formatInt(1234567)).toBe("1,234,567");
    expect(formatInt(1234.6)).toBe("1,235");
  });
});

describe("formatPercent", () => {
  it("defaults to one decimal place", () => {
    expect(formatPercent(23.456)).toBe("23.5%");
    expect(formatPercent(23.456, 2)).toBe("23.46%");
  });
});

describe("formatSignedPercentPoints", () => {
  it("adds a plus sign only for positive values", () => {
    expect(formatSignedPercentPoints(1.3)).toBe("+1.3 pp");
    expect(formatSignedPercentPoints(-2.9)).toBe("-2.9 pp");
    expect(formatSignedPercentPoints(0)).toBe("0.0 pp");
  });
});

describe("formatCompactTaka", () => {
  it("picks the right unit by magnitude", () => {
    expect(formatCompactTaka(1_748_802_083_320)).toBe("1,748.80B taka");
    expect(formatCompactTaka(51_927)).toBe("51.9K taka");
    expect(formatCompactTaka(500)).toBe("500 taka");
    expect(formatCompactTaka(2_500_000)).toBe("2.5M taka");
  });
});
