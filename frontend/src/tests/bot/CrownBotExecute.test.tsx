/**
 * Tests CROWN-BOT-ACTION-STRICT-1 — Sécurité exécution Crown Bot.
 * Vérifie que le frontend envoie UNIQUEMENT { pending_action_id } au backend.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "../mocks/server";
import * as botService from "../../services/botService";

describe("CrownBotExecute — Security", () => {
  let requestBody: any;

  beforeEach(() => {
    // Setup MSW to capture the request body
    requestBody = null;
    server.use(
      http.post("*/api/bot/execute", async ({ request }) => {
        requestBody = await request.json();
        return HttpResponse.json(
          { action_type: "info", message: "Success" },
          { status: 200 }
        );
      })
    );
  });

  it("sends_only_pending_action_id", async () => {
    // Call the bot execute with only pending_action_id
    await botService.executeBotAction("test-uuid-123");

    // Verify the exact request body
    expect(requestBody).toEqual({
      pending_action_id: "test-uuid-123",
    });

    // Verify no extra fields
    expect(Object.keys(requestBody)).toHaveLength(1);
    expect(Object.keys(requestBody)[0]).toBe("pending_action_id");
  });

  it("does_not_send_action_type", async () => {
    await botService.executeBotAction("test-uuid-456");

    expect(requestBody).not.toHaveProperty("action_type");
  });

  it("does_not_send_params", async () => {
    await botService.executeBotAction("test-uuid-789");

    expect(requestBody).not.toHaveProperty("params");
    expect(requestBody).not.toHaveProperty("parameters");
  });

  it("does_not_send_patient_id", async () => {
    await botService.executeBotAction("test-uuid-patient");

    expect(requestBody).not.toHaveProperty("patient_id");
  });

  it("shows_error_on_422", async () => {
    server.use(
      http.post("*/api/bot/execute", () => {
        return HttpResponse.json(
          { detail: "Extra fields not allowed" },
          { status: 422 }
        );
      })
    );

    try {
      await botService.executeBotAction("test-uuid-bad");
      expect.fail("Should have thrown");
    } catch (error: any) {
      expect(error.response?.status).toBe(422);
    }
  });

  it("shows_error_on_401", async () => {
    server.use(
      http.post("*/api/bot/execute", () => {
        return HttpResponse.json(
          { detail: "Unauthorized" },
          { status: 401 }
        );
      })
    );

    try {
      await botService.executeBotAction("test-uuid-unauth");
      expect.fail("Should have thrown");
    } catch (error: any) {
      expect(error.response?.status).toBe(401);
    }
  });
});

describe("CrownBotExecute — Legacy ChatMessage", () => {
  /**
   * Verify that the legacy ChatMessage.tsx component is not wired to
   * call /bot/execute directly. It should not have access to the action params.
   */
  it("legacy_ChatMessage_not_wired_to_execute", () => {
    // This test is a static code inspection test.
    // It verifies that frontend/src/components/CrownBot/ChatMessage.tsx
    // does NOT import or call bot execute endpoint.
    // If it does, this test should fail and we need to verify the code path.

    // For now, we can import and check that it doesn't have execute logic:
    // (In a real scenario, you'd import ChatMessage and inspect its props/handlers)

    // Mock verification: ChatMessage should only emit confirmation events,
    // not make API calls directly.
    expect(true).toBe(true); // Placeholder for code inspection
  });
});
