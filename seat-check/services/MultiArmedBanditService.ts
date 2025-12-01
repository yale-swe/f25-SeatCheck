// multi-Armed Bandit service for A/B/C button testing
export type ButtonVariant = 'A' | 'B' | 'C';

export interface VariantStats {
  variant: ButtonVariant;
  impressions: number;
  conversions: number;
  conversionRate: number;
}

export interface ButtonVariantConfig {
  variant: ButtonVariant;
  backgroundColor: string;
  text: string;
  borderRadius: number;
}

const STORAGE_KEY = 'multi_armed_bandit_stats';

// the 3 button variants we're testing
export const BUTTON_VARIANTS: Record<ButtonVariant, ButtonVariantConfig> = {
  A: {
    variant: 'A',
    backgroundColor: '#007AFF',
    text: 'Submit Check-in',
    borderRadius: 12,
  },
  B: {
    variant: 'B',
    backgroundColor: '#34C759',
    text: 'Check In Now',
    borderRadius: 20,
  },
  C: {
    variant: 'C',
    backgroundColor: '#FF9500',
    text: 'Submit',
    borderRadius: 8,
  },
};

class MultiArmedBanditService {
  private stats: Map<ButtonVariant, { impressions: number; conversions: number }>;
  private epsilon: number = 0.1; // exploration rate
  private minExplorationCount: number = 30; //min views before optimizing

  constructor() {
    this.stats = new Map([
      ['A', { impressions: 0, conversions: 0 }],
      ['B', { impressions: 0, conversions: 0 }],
      ['C', { impressions: 0, conversions: 0 }],
    ]);
    this.loadStats();
  }

  // Load saved stats from storage
  private async loadStats(): Promise<void> {
    try {
      const stored = await this.getStoredData();
      if (stored) {
        this.stats = new Map(Object.entries(stored) as [ButtonVariant, { impressions: number; conversions: number }][]);
      }
    } catch (error) {
      console.error('Failed to load MAB stats:', error);
    }
  }

  // Save current stats to storage
  private async saveStats(): Promise<void> {
    try {
      const statsObj = Object.fromEntries(this.stats);
      await this.setStoredData(statsObj);
    } catch (error) {
      console.error('Failed to save MAB stats:', error);
    }
  }

  private async getStoredData(): Promise<any> {
    if (typeof localStorage !== 'undefined') {
      const data = localStorage.getItem(STORAGE_KEY);
      return data ? JSON.parse(data) : null;
    }
    return null;
  }

  private async setStoredData(data: any): Promise<void> {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    }
  }

  // Calculate click rate for a variant
  private getConversionRate(variant: ButtonVariant): number {
    const stats = this.stats.get(variant);
    if (!stats || stats.impressions === 0) return 0;
    return stats.conversions / stats.impressions;
  }

  // Find the best performing variant
  private getBestVariant(): ButtonVariant {
    let bestVariant: ButtonVariant = 'A';
    let bestRate = -1;

    (['A', 'B', 'C'] as ButtonVariant[]).forEach((variant) => {
      const rate = this.getConversionRate(variant);
      if (rate > bestRate) {
        bestRate = rate;
        bestVariant = variant;
      }
    });

    return bestVariant;
  }

  // Pick a random variant (for exploration)
  private getRandomVariant(): ButtonVariant {
    const variants: ButtonVariant[] = ['A', 'B', 'C'];
    return variants[Math.floor(Math.random() * variants.length)];
  }

  // Find variant with fewest views
  private getLeastTestedVariant(): ButtonVariant {
    let leastVariant: ButtonVariant = 'A';
    let leastCount = Infinity;

    (['A', 'B', 'C'] as ButtonVariant[]).forEach((variant) => {
      const stats = this.stats.get(variant);
      if (stats && stats.impressions < leastCount) {
        leastCount = stats.impressions;
        leastVariant = variant;
      }
    });

    return leastVariant;
  }

  // Calculate exploration rate (decreases as we gather more data)
  private getDynamicEpsilon(): number {
    const totalImpressions = Array.from(this.stats.values()).reduce(
      (sum, s) => sum + s.impressions,
      0
    );

    const allHaveMinData = Array.from(this.stats.values()).every(
      (s) => s.impressions >= this.minExplorationCount
    );

    if (!allHaveMinData) {
      return 0.5; // explore more during initial phase
    }

    return Math.max(0.01, this.epsilon * Math.exp(-totalImpressions / 1000));
  }

  // Select which variant to show (main algorithm)
  public selectVariant(): ButtonVariant {
    const dynamicEpsilon = this.getDynamicEpsilon();

    // 1) Gather initial data - show variants with < 30 views
    const leastTested = this.getLeastTestedVariant();
    const leastStats = this.stats.get(leastTested);
    if (leastStats && leastStats.impressions < this.minExplorationCount) {
      return leastTested;
    }

    // 2) Epsilon-greedy: explore vs exploit
    if (Math.random() < dynamicEpsilon) {
      return this.getRandomVariant(); // explore
    } else {
      return this.getBestVariant(); // exploit
    }
  }

  // Record that a variant was shown
  public async recordImpression(variant: ButtonVariant): Promise<void> {
    const stats = this.stats.get(variant);
    if (stats) {
      stats.impressions++;
      await this.saveStats();
    }
  }

  // Record that a variant was clicked
  public async recordConversion(variant: ButtonVariant): Promise<void> {
    const stats = this.stats.get(variant);
    if (stats) {
      stats.conversions++;
      await this.saveStats();
    }
  }

  // Get current statistics for all variants
  public getStats(): VariantStats[] {
    return (['A', 'B', 'C'] as ButtonVariant[]).map((variant) => {
      const stats = this.stats.get(variant);
      return {
        variant,
        impressions: stats?.impressions || 0,
        conversions: stats?.conversions || 0,
        conversionRate: this.getConversionRate(variant),
      };
    });
  }

  // Reset all statistics
  public async resetStats(): Promise<void> {
    this.stats = new Map([
      ['A', { impressions: 0, conversions: 0 }],
      ['B', { impressions: 0, conversions: 0 }],
      ['C', { impressions: 0, conversions: 0 }],
    ]);
    await this.saveStats();
  }
}

export const banditService = new MultiArmedBanditService();
