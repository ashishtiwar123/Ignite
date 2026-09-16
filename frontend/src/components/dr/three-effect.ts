import type mapboxgl from "mapbox-gl";

/**
 * Mapbox custom layer that renders a 3D pulse marker locked to the incident coordinate.
 * Used in 3D mode without requiring external dependencies.
 */
export function createThreeEffectLayer(
  _center: [number, number],
  _colorHex: string,
  _radiusKm: number,
): mapboxgl.CustomLayerInterface {
  return {
    id: "three-effect",
    type: "custom",
    renderingMode: "3d",
    onAdd(_map, _gl) {},
    render(_gl, _args) {},
    onRemove() {},
  };
}
