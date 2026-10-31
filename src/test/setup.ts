import '@testing-library/react';
import { vi } from 'vitest';

if (typeof window !== 'undefined') {
  // Configure default base origin so URL and Request parsing in JSDOM succeeds cleanly without ERR_INVALID_URL
  if (!window.location.origin || window.location.origin === 'null') {
    try {
      Object.defineProperty(window.location, 'origin', {
        writable: true,
        configurable: true,
        value: 'http://localhost:3000',
      });
    } catch {}
  }

  // Mock window.matchMedia
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: (query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }),
  });

  // Mock Web Audio API for headless JSDOM testing
  if (typeof window.AudioContext === 'undefined') {
    class MockAudioNode {
      connect() {
        return this;
      }
      disconnect() {}
    }
    class MockGainNode extends MockAudioNode {
      gain = {
        value: 1,
        setValueAtTime: vi.fn(),
        exponentialRampToValueAtTime: vi.fn(),
        linearRampToValueAtTime: vi.fn(),
      };
    }
    class MockOscillatorNode extends MockAudioNode {
      type = 'sine';
      frequency = {
        value: 440,
        setValueAtTime: vi.fn(),
        exponentialRampToValueAtTime: vi.fn(),
      };
      start = vi.fn();
      stop = vi.fn();
    }
    class MockAnalyserNode extends MockAudioNode {
      fftSize = 64;
      smoothingTimeConstant = 0.8;
      frequencyBinCount = 32;
      getByteFrequencyData(arr: Uint8Array) {
        arr.fill(128);
      }
    }
    class MockAudioContext {
      state: AudioContextState = 'suspended';
      currentTime = 0;
      destination = new MockAudioNode();
      createGain() {
        return new MockGainNode();
      }
      createOscillator() {
        return new MockOscillatorNode();
      }
      createAnalyser() {
        return new MockAnalyserNode();
      }
      resume = vi.fn().mockImplementation(async () => {
        this.state = 'running';
      });
      suspend = vi.fn().mockImplementation(async () => {
        this.state = 'suspended';
      });
      close = vi.fn().mockImplementation(async () => {
        this.state = 'closed';
      });
    }
    (window as any).AudioContext = MockAudioContext;
    (window as any).webkitAudioContext = MockAudioContext;
  }
}

// Intercept Request constructor to resolve relative paths against base origin in Node/JSDOM
if (typeof globalThis.Request !== 'undefined') {
  const OriginalRequest = globalThis.Request;
  globalThis.Request = class RequestWithOrigin extends OriginalRequest {
    constructor(input: RequestInfo | URL, init?: RequestInit) {
      if (
        typeof input === 'string' &&
        !input.startsWith('http://') &&
        !input.startsWith('https://') &&
        !input.startsWith('data:') &&
        !input.startsWith('blob:')
      ) {
        const origin =
          typeof window !== 'undefined' && window.location?.origin && window.location.origin !== 'null'
            ? window.location.origin
            : 'http://localhost:3000';
        input = input.startsWith('/') ? `${origin}${input}` : `${origin}/${input}`;
      }
      super(input, init);
    }
  } as typeof Request;
}

if (typeof globalThis.fetch !== 'undefined') {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = function (input: RequestInfo | URL, init?: RequestInit) {
    if (
      typeof input === 'string' &&
      !input.startsWith('http://') &&
      !input.startsWith('https://') &&
      !input.startsWith('data:') &&
      !input.startsWith('blob:')
    ) {
      const origin =
        typeof window !== 'undefined' && window.location?.origin && window.location.origin !== 'null'
          ? window.location.origin
          : 'http://localhost:3000';
      input = input.startsWith('/') ? `${origin}${input}` : `${origin}/${input}`;
    }
    return originalFetch(input, init);
  };
}

if (typeof Element !== 'undefined') {
  // Mock Element.prototype.scrollIntoView
  Element.prototype.scrollIntoView = () => {};
}

if (typeof HTMLCanvasElement !== 'undefined') {
  // Mock HTMLCanvasElement.prototype.getContext for headless JSDOM WebGL tests
  HTMLCanvasElement.prototype.getContext = function (this: HTMLCanvasElement, contextType: string) {
  if (contextType === 'webgl' || contextType === 'webgl2' || contextType === 'experimental-webgl') {
    const baseContext = {
      canvas: this,
      drawingBufferWidth: 800,
      drawingBufferHeight: 600,
      VERSION: 7938,
      SHADING_LANGUAGE_VERSION: 7937,
      VENDOR: 7936,
      getContextAttributes: () => ({
        alpha: true,
        depth: true,
        stencil: true,
        antialias: true,
        premultipliedAlpha: true,
        preserveDrawingBuffer: false,
      }),
      isContextLost: () => false,
      getParameter: (param: any) => {
        if (!param || param === 7938) return 'WebGL 2.0';
        if (param === 7937) return 'WebGL GLSL ES 3.00';
        if (param === 7936) return 'WebKit';
        if (param === 34047) return 16; // MAX_VERTEX_TEXTURE_IMAGE_UNITS
        if (param === 34930) return 16; // MAX_TEXTURE_IMAGE_UNITS
        if (param === 3379) return 4096; // MAX_TEXTURE_SIZE
        if (param === 34076) return 4096; // MAX_CUBE_MAP_TEXTURE_SIZE
        if (param === 34921) return 16; // MAX_VERTEX_ATTRIBS
        if (param === 36347) return 1024; // MAX_VERTEX_UNIFORM_VECTORS
        if (param === 36348) return 30; // MAX_VARYING_VECTORS
        if (param === 36349) return 1024; // MAX_FRAGMENT_UNIFORM_VECTORS
        if (param === 36183) return 4; // MAX_SAMPLES
        if (param === 32937) return 0; // SAMPLES
        return 0;
      },
      getExtension: () => null,
      getShaderPrecisionFormat: () => ({ rangeMin: 1, rangeMax: 1, precision: 1 }),
      getShaderParameter: (_shader: any, pname: any) => {
        if (pname === 35713) return true; // COMPILE_STATUS
        return true;
      },
      getProgramParameter: (_program: any, pname: any) => {
        if (pname === 35714 || pname === 35715 || pname === 0x91b1) return true; // LINK_STATUS, VALIDATE_STATUS, COMPLETION_STATUS_KHR
        if (pname === 35718 || pname === 35721) return 0; // ACTIVE_UNIFORMS, ACTIVE_ATTRIBUTES
        return 0;
      },
      getActiveUniform: () => ({ name: 'dummy_uniform', size: 1, type: 35664 }),
      getActiveAttrib: () => ({ name: 'dummy_attrib', size: 1, type: 35664 }),
      getProgramInfoLog: () => '',
      getShaderInfoLog: () => '',
      createTexture: () => ({}),
      createBuffer: () => ({}),
      createProgram: () => ({}),
      createShader: () => ({}),
      createFramebuffer: () => ({}),
      createRenderbuffer: () => ({}),
      createVertexArray: () => ({}),
      getUniformLocation: () => ({}),
      getAttribLocation: () => 0,
      getUniformBlockIndex: () => 0,
    };
    const WEBGL_CONSTANTS: Record<string, number> = {
      POINTS: 0,
      LINES: 1,
      LINE_LOOP: 2,
      LINE_STRIP: 3,
      TRIANGLES: 4,
      TRIANGLE_STRIP: 5,
      TRIANGLE_FAN: 6,
      ZERO: 0,
      ONE: 1,
      SRC_COLOR: 0x0300,
      ONE_MINUS_SRC_COLOR: 0x0301,
      SRC_ALPHA: 0x0302,
      ONE_MINUS_SRC_ALPHA: 0x0303,
      DST_ALPHA: 0x0304,
      ONE_MINUS_DST_ALPHA: 0x0305,
      DST_COLOR: 0x0306,
      ONE_MINUS_DST_COLOR: 0x0307,
      SRC_ALPHA_SATURATE: 0x0308,
      FUNC_ADD: 0x8006,
      BLEND_EQUATION: 0x8009,
      BLEND_EQUATION_RGB: 0x8009,
      BLEND_EQUATION_ALPHA: 0x883d,
      FUNC_SUBTRACT: 0x800a,
      FUNC_REVERSE_SUBTRACT: 0x800b,
      BLEND_DST_RGB: 0x80c8,
      BLEND_SRC_RGB: 0x80c9,
      BLEND_DST_ALPHA: 0x80ca,
      BLEND_SRC_ALPHA: 0x80cb,
      ARRAY_BUFFER: 0x8892,
      ELEMENT_ARRAY_BUFFER: 0x8893,
      ARRAY_BUFFER_BINDING: 0x8894,
      ELEMENT_ARRAY_BUFFER_BINDING: 0x8895,
      STREAM_DRAW: 0x88e0,
      STATIC_DRAW: 0x88e4,
      DYNAMIC_DRAW: 0x88e8,
      BYTE: 0x1400,
      UNSIGNED_BYTE: 0x1401,
      SHORT: 0x1402,
      UNSIGNED_SHORT: 0x1403,
      INT: 0x1404,
      UNSIGNED_INT: 0x1405,
      FLOAT: 0x1406,
      HALF_FLOAT: 0x140b,
      TEXTURE_2D: 0x0de1,
      TEXTURE_CUBE_MAP: 0x8513,
      TEXTURE_BINDING_2D: 0x8069,
      TEXTURE_BINDING_CUBE_MAP: 0x806b,
      TEXTURE_WRAP_S: 0x2802,
      TEXTURE_WRAP_T: 0x2803,
      TEXTURE_MAG_FILTER: 0x2800,
      TEXTURE_MIN_FILTER: 0x2801,
      NEAREST: 0x2600,
      LINEAR: 0x2601,
      REPEAT: 0x2901,
      CLAMP_TO_EDGE: 0x812f,
      MIRRORED_REPEAT: 0x8370,
      TEXTURE0: 0x84c0,
      ACTIVE_TEXTURE: 0x84e0,
      FRAMEBUFFER: 0x8d40,
      RENDERBUFFER: 0x8d41,
      COLOR_ATTACHMENT0: 0x8ce0,
      DEPTH_ATTACHMENT: 0x8d00,
      STENCIL_ATTACHMENT: 0x8d20,
      DEPTH_STENCIL_ATTACHMENT: 0x821a,
      FRAMEBUFFER_COMPLETE: 0x8cd5,
      COLOR_BUFFER_BIT: 0x00004000,
      DEPTH_BUFFER_BIT: 0x00000100,
      STENCIL_BUFFER_BIT: 0x00000400,
    };
    return new Proxy(baseContext, {
      get(target, prop) {
        if (prop in target) return (target as any)[prop];
        if (typeof prop === 'string' && prop in WEBGL_CONSTANTS) return WEBGL_CONSTANTS[prop];
        if (typeof prop === 'string' && prop === prop.toUpperCase() && prop.length > 2) return 0;
        return () => {};
      },
    });
  }
  return null;
} as any;
}

