import { billingResponse } from '../../scripts/billing-proxy.mjs';

export default async function billing(event: {req: Request}, next: () => unknown | Promise<unknown>) {
  return (await billingResponse(event.req)) ?? next();
}
