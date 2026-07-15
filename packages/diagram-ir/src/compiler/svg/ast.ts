export type SvgNode = SvgElement | SvgText;

export type SvgElement = {
  kind: "element";
  name: string;
  attributes: SvgAttribute[];
  children: SvgNode[];
};

export type SvgText = {
  kind: "text";
  value: string;
};

export type SvgAttribute = {
  name: string;
  value: string;
};
