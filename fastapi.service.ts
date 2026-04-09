import { Injectable, InternalServerErrorException } from '@nestjs/common';

@Injectable()
export class FastapiService {
  private readonly baseUrl: string;

  constructor() {
    this.baseUrl = process.env.FASTAPI_URL || process.env.NEXT_PUBLIC_FASTAPI_BASE_URL || '';
    if (!this.baseUrl) {
      throw new InternalServerErrorException('FASTAPI_URL is not configured');
    }
  }

  private buildUrl(path: string): string {
    const cleanBase = this.baseUrl.replace(/\/+$/, '');
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    return `${cleanBase}${cleanPath}`;
  }

  async get(path: string, headers?: Record<string, string>) {
    const res = await fetch(this.buildUrl(path), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...(headers || {}),
      },
    });

    const text = await res.text();
    const data = text ? this.safeJsonParse(text) : null;

    if (!res.ok) {
      throw new Error(
        `FastAPI GET ${path} failed with ${res.status}: ${text || 'no body'}`
      );
    }

    return data;
  }

  async post(path: string, body?: unknown, headers?: Record<string, string>) {
    const res = await fetch(this.buildUrl(path), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(headers || {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    });

    const text = await res.text();
    const data = text ? this.safeJsonParse(text) : null;

    if (!res.ok) {
      throw new Error(
        `FastAPI POST ${path} failed with ${res.status}: ${text || 'no body'}`
      );
    }

    return data;
  }

  private safeJsonParse(text: string) {
    try {
      return JSON.parse(text);
    } catch {
      return { raw: text };
    }
  }
}