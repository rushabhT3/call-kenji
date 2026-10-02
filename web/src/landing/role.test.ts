import { describe, expect, it } from "vitest";
import account from "../../../content/account.yaml?raw";
import { ROLE } from "./role.ts";

describe("role card", () => {
  it("shows the same fictional account the agent uses", () => {
    expect(account).toContain(`written_name: ${ROLE.nameJa}`);
    expect(account).toContain(`date_of_birth: ${ROLE.dateOfBirth}`);
    expect(account).toContain(`account_suffix: "${ROLE.accountSuffix}"`);
    expect(account).toContain(`balance_yen: ${String(ROLE.balanceYen)}`);
    expect(account).toContain(`overdue_since: ${ROLE.overdueSince}`);
  });
});
