from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import moderngl
import numpy as np

VERTEX_SHADER = """
#version 330
in vec2 in_pos;
in vec2 in_uv;
out vec2 uv;
void main() {
    gl_Position = vec4(in_pos, 0.0, 1.0);
    uv = in_uv;
}
"""

FULLSCREEN_VERTICES = np.array(
    [
        -1.0, -1.0, 0.0, 0.0,
         1.0, -1.0, 1.0, 0.0,
        -1.0,  1.0, 0.0, 1.0,
        -1.0,  1.0, 0.0, 1.0,
         1.0, -1.0, 1.0, 0.0,
         1.0,  1.0, 1.0, 1.0,
    ],
    dtype="f4",
)


@dataclass(frozen=True)
class RenderedWorkload:
    actual: np.ndarray
    expected: np.ndarray


class GraphicsSession:
    def __init__(self, backend: str = "auto", minimum_gl_version: int = 330) -> None:
        kwargs = {"require": minimum_gl_version}
        if backend != "auto":
            kwargs["backend"] = backend
        self.context = moderngl.create_standalone_context(**kwargs)

    @property
    def capabilities(self) -> dict[str, object]:
        info = self.context.info
        return {
            "version_code": self.context.version_code,
            "vendor": info.get("GL_VENDOR", "unknown"),
            "renderer": info.get("GL_RENDERER", "unknown"),
            "version": info.get("GL_VERSION", "unknown"),
            "glsl_version": info.get("GL_SHADING_LANGUAGE_VERSION", "unknown"),
            "max_texture_size": info.get("GL_MAX_TEXTURE_SIZE"),
        }

    def close(self) -> None:
        self.context.release()

    def invalid_shader_probe(self) -> str:
        invalid_fragment = """
        #version 330
        out vec4 fragColor;
        void main() { fragColor = vec4(this_symbol_does_not_exist); }
        """
        try:
            self.context.program(vertex_shader=VERTEX_SHADER, fragment_shader=invalid_fragment)
        except Exception as exc:  # ModernGL exposes backend compiler text through Error.
            return str(exc).strip()
        raise RuntimeError("invalid shader unexpectedly compiled")

    def render(self, workload: str, width: int, height: int) -> RenderedWorkload:
        renderers: dict[str, Callable[[int, int], RenderedWorkload]] = {
            "solid_color": self._solid_color,
            "texture_quadrants": self._texture_quadrants,
            "alpha_blend": self._alpha_blend,
            "depth_overlap": self._depth_overlap,
        }
        try:
            renderer = renderers[workload]
        except KeyError as exc:
            raise ValueError(f"unknown workload: {workload}") from exc
        return renderer(width, height)

    def _framebuffer(self, width: int, height: int, depth: bool = False):
        color = self.context.renderbuffer((width, height), components=4, dtype="f1")
        depth_attachment = self.context.depth_renderbuffer((width, height)) if depth else None
        return self.context.framebuffer(
            color_attachments=[color], depth_attachment=depth_attachment
        )

    @staticmethod
    def _read_rgb(framebuffer, width: int, height: int) -> np.ndarray:
        raw = framebuffer.read(components=3, alignment=1)
        return np.frombuffer(raw, dtype=np.uint8).reshape((height, width, 3)).copy()

    def _fullscreen_program(self, fragment_shader: str):
        program = self.context.program(
            vertex_shader=VERTEX_SHADER, fragment_shader=fragment_shader
        )
        buffer = self.context.buffer(FULLSCREEN_VERTICES.tobytes())
        vao = self.context.vertex_array(program, [(buffer, "2f 2f", "in_pos", "in_uv")])
        return program, buffer, vao

    def _solid_color(self, width: int, height: int) -> RenderedWorkload:
        fragment = """
        #version 330
        uniform vec3 color;
        out vec4 fragColor;
        void main() { fragColor = vec4(color, 1.0); }
        """
        fbo = self._framebuffer(width, height)
        program, buffer, vao = self._fullscreen_program(fragment)
        try:
            fbo.use()
            self.context.disable(moderngl.BLEND | moderngl.DEPTH_TEST)
            fbo.clear(0.0, 0.0, 0.0, 1.0)
            program["color"].value = (0.125, 0.5, 0.875)
            vao.render(moderngl.TRIANGLES)
            self.context.finish()
            actual = self._read_rgb(fbo, width, height)
            expected = np.empty_like(actual)
            expected[:, :, :] = np.array([32, 128, 223], dtype=np.uint8)
            return RenderedWorkload(actual, expected)
        finally:
            vao.release()
            buffer.release()
            program.release()
            fbo.release()

    def _texture_quadrants(self, width: int, height: int) -> RenderedWorkload:
        fragment = """
        #version 330
        in vec2 uv;
        uniform sampler2D source_texture;
        out vec4 fragColor;
        void main() { fragColor = texture(source_texture, uv); }
        """
        fbo = self._framebuffer(width, height)
        program, buffer, vao = self._fullscreen_program(fragment)
        pixels = bytes(
            [
                255, 0, 0, 255,      0, 255, 0, 255,
                0, 0, 255, 255,      255, 255, 255, 255,
            ]
        )
        texture = self.context.texture((2, 2), 4, data=pixels, alignment=1)
        texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
        texture.repeat_x = False
        texture.repeat_y = False
        try:
            fbo.use()
            self.context.disable(moderngl.BLEND | moderngl.DEPTH_TEST)
            texture.use(location=0)
            program["source_texture"].value = 0
            vao.render(moderngl.TRIANGLES)
            self.context.finish()
            actual = self._read_rgb(fbo, width, height)
            expected = np.empty_like(actual)
            split_x, split_y = width // 2, height // 2
            expected[:split_y, :split_x] = (255, 0, 0)
            expected[:split_y, split_x:] = (0, 255, 0)
            expected[split_y:, :split_x] = (0, 0, 255)
            expected[split_y:, split_x:] = (255, 255, 255)
            return RenderedWorkload(actual, expected)
        finally:
            texture.release()
            vao.release()
            buffer.release()
            program.release()
            fbo.release()

    def _alpha_blend(self, width: int, height: int) -> RenderedWorkload:
        fragment = """
        #version 330
        uniform vec4 color;
        out vec4 fragColor;
        void main() { fragColor = color; }
        """
        fbo = self._framebuffer(width, height)
        program, buffer, vao = self._fullscreen_program(fragment)
        try:
            fbo.use()
            self.context.disable(moderngl.DEPTH_TEST)
            self.context.disable(moderngl.BLEND)
            fbo.clear(0.0, 0.0, 1.0, 1.0)
            self.context.enable(moderngl.BLEND)
            self.context.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
            program["color"].value = (1.0, 0.0, 0.0, 0.25)
            vao.render(moderngl.TRIANGLES)
            self.context.finish()
            actual = self._read_rgb(fbo, width, height)
            expected = np.empty_like(actual)
            expected[:, :, :] = np.array([64, 0, 191], dtype=np.uint8)
            return RenderedWorkload(actual, expected)
        finally:
            self.context.disable(moderngl.BLEND)
            vao.release()
            buffer.release()
            program.release()
            fbo.release()

    def _depth_overlap(self, width: int, height: int) -> RenderedWorkload:
        vertex = """
        #version 330
        in vec3 in_pos;
        void main() { gl_Position = vec4(in_pos, 1.0); }
        """
        fragment = """
        #version 330
        uniform vec3 color;
        out vec4 fragColor;
        void main() { fragColor = vec4(color, 1.0); }
        """
        program = self.context.program(vertex_shader=vertex, fragment_shader=fragment)
        near_vertices = np.array([-0.8, -0.8, -0.5, 0.8, -0.8, -0.5, 0.0, 0.8, -0.5], dtype="f4")
        far_vertices = np.array([-0.8, -0.8, 0.5, 0.8, -0.8, 0.5, 0.0, 0.8, 0.5], dtype="f4")
        near_buffer = self.context.buffer(near_vertices.tobytes())
        far_buffer = self.context.buffer(far_vertices.tobytes())
        near_vao = self.context.vertex_array(program, [(near_buffer, "3f", "in_pos")])
        far_vao = self.context.vertex_array(program, [(far_buffer, "3f", "in_pos")])
        fbo = self._framebuffer(width, height, depth=True)
        try:
            fbo.use()
            fbo.clear(0.0, 0.0, 0.0, 1.0, depth=1.0)
            self.context.disable(moderngl.BLEND)
            self.context.enable(moderngl.DEPTH_TEST)
            program["color"].value = (0.0, 1.0, 0.0)
            near_vao.render(moderngl.TRIANGLES)
            program["color"].value = (1.0, 0.0, 0.0)
            far_vao.render(moderngl.TRIANGLES)
            self.context.finish()
            actual = self._read_rgb(fbo, width, height)
            expected = actual.copy()
            center = (height // 2, width // 2)
            expected[center] = (0, 255, 0)
            expected[0, 0] = (0, 0, 0)
            actual_for_compare = actual.copy()
            # Ignore raster-edge differences: validate two unambiguous probes and color leakage.
            mask = np.ones((height, width), dtype=bool)
            mask[center] = False
            mask[0, 0] = False
            expected[mask] = actual_for_compare[mask]
            red_leak = np.all(actual == np.array([255, 0, 0], dtype=np.uint8), axis=2)
            if np.any(red_leak):
                expected[red_leak] = (0, 255, 0)
            return RenderedWorkload(actual_for_compare, expected)
        finally:
            self.context.disable(moderngl.DEPTH_TEST)
            near_vao.release()
            far_vao.release()
            near_buffer.release()
            far_buffer.release()
            program.release()
            fbo.release()
