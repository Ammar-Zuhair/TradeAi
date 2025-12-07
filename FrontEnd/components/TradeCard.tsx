import React from 'react';
import { View, StyleSheet, TouchableOpacity } from 'react-native';
import { SubheadingText, BodyText } from './StyledText';
import { useTheme } from '@/contexts/ThemeContext';
import Layout from '@/constants/Layout';
import { ArrowDown, ArrowUp } from 'lucide-react-native';

export type TradeType = {
  id: string;
  symbol: string;
  direction: 'BUY' | 'SELL';
  openPrice: number;
  currentPrice: number;
  size?: number;
  profit: number;
  openTime: string;
  closeTime?: string;
  status: 'OPEN' | 'CLOSED';
  ticket?: number;
};

type TradeCardProps = {
  trade: TradeType;
  onPress?: (id: string) => void;
};

export default function TradeCard({ trade, onPress }: TradeCardProps) {
  const { colors } = useTheme();
  const isProfit = trade.profit > 0;
  const profitColor = isProfit ? colors.positive : colors.negative;
  const profitPercentage = ((trade.currentPrice - trade.openPrice) / trade.openPrice) * 100 * (trade.direction === 'BUY' ? 1 : -1);

  // Dynamic styles
  const themeStyles = {
    container: { backgroundColor: colors.card },
    symbol: { color: colors.text },
    detailLabel: { color: colors.placeholder },
    detailValue: { color: colors.text },
  };

  return (
    <TouchableOpacity
      style={[styles.container, themeStyles.container]}
      onPress={() => onPress && onPress(trade.id)}
      activeOpacity={0.7}
    >
      <View style={styles.symbolContainer}>
        <SubheadingText style={[styles.symbol, themeStyles.symbol]}>{trade.symbol}</SubheadingText>
        <View style={[styles.directionBadge, {
          backgroundColor: trade.direction === 'BUY' ? colors.positive : colors.negative
        }]}>
          {trade.direction === 'BUY' ?
            <ArrowUp size={14} color="#fff" /> :
            <ArrowDown size={14} color="#fff" />
          }
          <BodyText style={styles.directionText}>{trade.direction}</BodyText>
        </View>
      </View>

      <View style={styles.detailsContainer}>
        <View style={styles.detailRow}>
          <BodyText style={[styles.detailLabel, themeStyles.detailLabel]}>Entry</BodyText>
          <BodyText style={[styles.detailValue, themeStyles.detailValue]}>${trade.openPrice.toFixed(2)}</BodyText>
        </View>
        <View style={styles.detailRow}>
          <BodyText style={[styles.detailLabel, themeStyles.detailLabel]}>Current</BodyText>
          <BodyText style={[styles.detailValue, themeStyles.detailValue]}>${trade.currentPrice.toFixed(2)}</BodyText>
        </View>
        <View style={styles.detailRow}>
          <BodyText style={[styles.detailLabel, themeStyles.detailLabel]}>Ticket</BodyText>
          <BodyText style={[styles.detailValue, themeStyles.detailValue]}>{trade.ticket || '-'}</BodyText>
        </View>
      </View>

      <View style={styles.profitContainer}>
        <SubheadingText style={[styles.profitValue, { color: profitColor }]}>
          ${Math.abs(trade.profit).toFixed(2)}
        </SubheadingText>
        <BodyText style={[styles.profitPercentage, { color: profitColor }]}>
          {isProfit ? '+' : '-'}{Math.abs(profitPercentage).toFixed(2)}%
        </BodyText>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    borderRadius: Layout.borderRadius.lg,
    padding: Layout.spacing.md,
    marginBottom: Layout.spacing.md,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  symbolContainer: {
    flexDirection: 'column',
    alignItems: 'flex-start',
    justifyContent: 'center',
    flex: 1,
  },
  symbol: {
    fontSize: 18,
    marginBottom: Layout.spacing.xs,
  },
  directionBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Layout.spacing.sm,
    paddingVertical: Layout.spacing.xs,
    borderRadius: Layout.borderRadius.sm,
  },
  directionText: {
    color: '#fff',
    fontSize: 12,
    marginLeft: 2,
  },
  detailsContainer: {
    flex: 1,
    marginLeft: Layout.spacing.md,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: Layout.spacing.xs,
  },
  detailLabel: {
    fontSize: 14,
  },
  detailValue: {
    fontSize: 14,
  },
  profitContainer: {
    alignItems: 'flex-end',
    flex: 1,
  },
  profitValue: {
    fontSize: 18,
  },
  profitPercentage: {
    fontSize: 14,
  },
});