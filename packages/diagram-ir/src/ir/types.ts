import type { Static } from "@sinclair/typebox";

import type {
  DiagramIrV01aSchema,
  EdgeV01aSchema,
  MetadataV01aSchema,
  NodeRoleSchema,
  NodeV01aSchema
} from "./schema.js";

export type NodeRole = Static<typeof NodeRoleSchema>;
export type NodeV01a = Static<typeof NodeV01aSchema>;
export type EdgeV01a = Static<typeof EdgeV01aSchema>;
export type MetadataV01a = Static<typeof MetadataV01aSchema>;
export type DiagramIrV01a = Static<typeof DiagramIrV01aSchema>;
