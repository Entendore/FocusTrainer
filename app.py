import sys
import os
import math
import struct
import wave
import random
import time
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QStackedWidget, QPushButton, QLabel,
    QSizePolicy, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QFont, QColor, QCursor
from PySide6.QtMultimedia import QSoundEffect

# --- Audio Engine ---
class SoundEngine:
    def __init__(self):
        self.sounds = {}
        self.temp_dir = os.path.join(os.path.expanduser("~"), ".focus_trainer_sounds")
        os.makedirs(self.temp_dir, exist_ok=True)
        self._generate_sounds()

    def _make_wav(self, filename, frequencies, duration=0.15, volume=0.3, wave_type='sine'):
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        filepath = os.path.join(self.temp_dir, filename)
        with wave.open(filepath, 'w') as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sample_rate)
            for i in range(n_samples):
                t = float(i) / sample_rate
                if isinstance(frequencies[0], tuple):
                    freq = frequencies[0][1]
                    for j in range(1, len(frequencies)):
                        if t <= frequencies[j][0]:
                            t0, f0 = frequencies[j-1]; t1, f1 = frequencies[j]
                            if t1 > t0: freq = f0 + (f1 - f0) * ((t - t0) / (t1 - t0))
                            break
                        else: freq = frequencies[-1][1]
                else: freq = frequencies[0]
                val = math.sin(2.0 * math.pi * freq * t) if wave_type == 'sine' else 2.0 * (t * freq - math.floor(t * freq + 0.5))
                val = int(volume * 32767.0 * max(-1.0, min(1.0, val)))
                wf.writeframesraw(struct.pack('<h', val))
        sound = QSoundEffect()
        sound.setSource(QUrl.fromLocalFile(os.path.abspath(filepath)))
        sound.setVolume(0.5)
        self.sounds[filename] = sound

    def _generate_sounds(self):
        self._make_wav("ok.wav", [(0, 780), (0.06, 1040)], duration=0.15, volume=0.3)
        self._make_wav("err.wav", [180], duration=0.25, volume=0.2, wave_type='sawtooth')
        self._make_wav("tick.wav", [600], duration=0.06, volume=0.15)
        self._make_wav("go.wav", [(0, 520), (0.08, 780), (0.16, 1040)], duration=0.3, volume=0.3)
        self._make_wav("complete.wav", [(0, 520), (0.12, 660), (0.24, 780), (0.36, 1040)], duration=0.55, volume=0.3)

    def play(self, name):
        if name in self.sounds: self.sounds[name].play()

# --- Global Stylesheet ---
STYLE_SHEET = """
QMainWindow, QWidget { background-color: #08080E; color: #F0ECE3; }
QLabel { background-color: transparent; }
QPushButton { border: none; padding: 8px; border-radius: 8px; }
QPushButton:hover { cursor: pointer; }
#hubTitle { font-size: 64px; font-weight: 800; letter-spacing: -2px; }
#hubTitle span { color: #E8963A; }
#hubSub { color: #7A7690; font-size: 16px; font-weight: 300; margin-top: 8px; }
#sectionLabel { color: #7A7690; font-size: 12px; text-transform: uppercase; letter-spacing: 2px; font-weight: 600; }
.modeCard { background-color: #16161F; border: 1px solid #2A2A38; border-radius: 14px; padding: 16px; text-align: left; min-height: 130px; }
.modeCard:hover { background-color: #1E1E2A; border-color: #B8742A; }
#mcIcon { width: 40px; height: 40px; border-radius: 10px; background-color: rgba(232,150,58,0.1); color: #E8963A; font-size: 20px; font-weight: bold; }
#mcName { font-size: 16px; font-weight: 700; margin-top: 8px; }
#mcDesc { color: #7A7690; font-size: 11px; margin-top: 4px; line-height: 1.3; }
#mcBest { color: #E8963A; font-family: 'Courier New', monospace; font-size: 11px; margin-top: 8px; }
#statsBar { color: #7A7690; font-family: 'Courier New', monospace; font-size: 13px; }
#statsBar b { color: #F0ECE3; font-weight: 600; }
#gameHeader { background-color: rgba(8,8,14,0.9); border-bottom: 1px solid #2A2A38; padding: 8px 16px; }
#backBtn { background-color: transparent; border: 1px solid #2A2A38; color: #7A7690; width: 36px; height: 36px; border-radius: 8px; font-size: 16px; }
#backBtn:hover { border-color: #E8963A; color: #E8963A; }
#gameTitle { font-weight: 600; font-size: 14px; letter-spacing: 1px; }
.statChip { color: #7A7690; font-family: 'Courier New', monospace; font-size: 14px; }
.statChip b { font-weight: 600; }
#scoreChip b { color: #E8963A; }
#gameFooter { background-color: rgba(8,8,14,0.9); border-top: 1px solid #2A2A38; color: #7A7690; font-size: 14px; padding: 12px; }
.targetCell { background-color: #16161F; border: 1px solid #2A2A38; border-radius: 10px; font-size: 24px; font-weight: bold; }
.targetCell:hover { background-color: #1E1E2A; }
.isTarget { background-color: #E8963A; border-color: #E8963A; color: #000; }
.isCorrect { background-color: #34D399; border-color: #34D399; color: #000; }
.isWrong { background-color: #EF4444; border-color: #EF4444; color: #fff; }
.isMissed { background-color: rgba(239,68,68,0.2); border-color: rgba(239,68,68,0.5); }
#stroopWord { font-size: 72px; font-weight: 800; }
.stroopBtn { padding: 16px; border-radius: 11px; font-weight: 700; font-size: 16px; color: #000000; text-transform: uppercase; letter-spacing: 1px; }
#seqDisplay { font-size: 120px; font-weight: 700; font-family: 'Courier New', monospace; color: #E8963A; }
.seqDigit { width: 44px; height: 44px; border-radius: 9px; border: 2px solid #2A2A38; font-family: 'Courier New', monospace; font-weight: 700; font-size: 18px; background-color: transparent; }
.seqDigit.filled { border-color: #E8963A; color: #E8963A; background-color: rgba(232,150,58,0.1); }
.seqDigit.correct { border-color: #34D399; color: #34D399; background-color: rgba(52,211,153,0.2); }
.seqDigit.wrong { border-color: #EF4444; color: #EF4444; background-color: rgba(239,68,68,0.2); }
.numBtn { background-color: #16161F; border: 1px solid #2A2A38; color: #F0ECE3; font-size: 24px; font-family: 'Courier New', monospace; font-weight: 700; border-radius: 9px; padding: 12px; }
.numBtn:hover { background-color: #1E1E2A; border-color: #B8742A; }
.numBtn.action { font-size: 18px; font-family: sans-serif; }
.schulteCell { background-color: #16161F; border: 1px solid #2A2A38; border-radius: 8px; font-size: 22px; font-weight: 700; font-family: 'Courier New', monospace; color: #F0ECE3; }
.schulteCell:hover { background-color: #1E1E2A; }
.schulteCell.found { background-color: rgba(52,211,153,0.15); border-color: #34D399; color: #34D399; }
.schulteCell.wrong { background-color: rgba(239,68,68,0.2); border-color: #EF4444; color: #EF4444; }
.nbackCell { background-color: #16161F; border: 2px solid #2A2A38; border-radius: 10px; }
.nbackCell.active { background-color: #E8963A; border-color: #E8963A; }
.nbackCell.history { background-color: rgba(232,150,58,0.15); border-color: rgba(232,150,58,0.4); }
.nbackBtn { background-color: #16161F; border: 1px solid #2A2A38; color: #F0ECE3; padding: 16px 32px; border-radius: 10px; font-weight: 700; font-size: 16px; }
.nbackBtn:hover { background-color: #1E1E2A; border-color: #B8742A; }
.nbackBtn.match { border-color: #E8963A; color: #E8963A; }
#gonogoLetter { font-size: 160px; font-weight: 800; font-family: 'Courier New', monospace; color: #F0ECE3; }
#gonogoFeedback { font-size: 24px; font-weight: 700; }
#flankerArrows { font-size: 100px; font-weight: 800; font-family: 'Courier New', monospace; letter-spacing: 8px; color: #F0ECE3; }
.flankerBtn { background-color: #16161F; border: 1px solid #2A2A38; color: #F0ECE3; padding: 20px 40px; border-radius: 12px; font-size: 36px; font-weight: bold; }
.flankerBtn:hover { background-color: #1E1E2A; border-color: #B8742A; }
#flankerFeedback { font-size: 20px; font-weight: 600; }
.patternCell { background-color: #16161F; border: 2px solid #2A2A38; border-radius: 10px; }
.patternCell.active { background-color: #E8963A; border-color: #E8963A; }
.patternCell.found { background-color: rgba(52,211,153,0.2); border-color: #34D399; }
.patternCell.wrong { background-color: rgba(239,68,68,0.2); border-color: #EF4444; }
"""

class FocusTrainer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Focus Trainer — 8-Mode Brain Training")
        self.resize(1000, 750)
        self.setMinimumSize(800, 600)
        self.setStyleSheet(STYLE_SHEET)
        self.sound = SoundEngine()
        self.settings = self._load_settings()
        self.current_mode = None
        self.game_active = False
        self.timers = []
        self.start_time = 0
        self.init_ui()

    def _load_settings(self):
        return {f"{m}_best": 0 for m in ["target", "stroop", "sequence", "schulte", "nback", "gonogo", "flanker", "pattern"]}

    def _save_settings(self): pass

    def init_ui(self):
        central = QWidget(); self.setCentralWidget(central)
        main_layout = QVBoxLayout(central); main_layout.setContentsMargins(0,0,0,0); main_layout.setSpacing(0)
        self.stack = QStackedWidget(); main_layout.addWidget(self.stack)
        self.hub_screen = self.create_hub()
        self.game_screen = self.create_game()
        self.results_screen = self.create_results()
        self.countdown_overlay = self.create_countdown()
        self.stack.addWidget(self.hub_screen); self.stack.addWidget(self.game_screen); self.stack.addWidget(self.results_screen)
        self.stack.setCurrentIndex(0)

    def clear_timers(self):
        for t in self.timers: t.stop()
        self.timers.clear()

    def clear_layout(self, layout):
        if not layout: return
        while layout.count():
            item = layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            elif item.layout(): self.clear_layout(item.layout())

    def elapsed_ms(self): return int(time.perf_counter() * 1000)

    # --- HUB SCREEN ---
    def create_hub(self):
        w = QWidget(); lay = QVBoxLayout(w); lay.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.setSpacing(24)
        title = QLabel("FOC<span>US</span>"); title.setObjectName("hubTitle"); title.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(title)
        sub = QLabel("Train your attention. Eight modes, one goal."); sub.setObjectName("hubSub"); sub.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(sub)
        lay.addSpacing(10)
        lbl = QLabel("Brain Training"); lbl.setObjectName("sectionLabel"); lay.addWidget(lbl)
        grid = QGridLayout(); grid.setSpacing(12); lay.addLayout(grid)
        
        modes = [
            ("Target Spotter", "⊕", "Locate highlighted targets on an escalating grid.", "target"),
            ("Stroop Challenge", "◐", "Name the ink color, not the word itself.", "stroop"),
            ("Number Sequence", "123", "Memorize and recall growing digit strings.", "sequence"),
            ("Schulte Table", "▦", "Find numbers 1-25 in order. Visual scanning.", "schulte"),
            ("N-Back Memory", "⟲", "Match current position to 2 steps back.", "nback"),
            ("Go / No-Go", "⚡", "Respond to letters, withhold for X. Impulse control.", "gonogo"),
            ("Flanker Task", "↔", "Identify center arrow, ignoring distractions.", "flanker"),
            ("Pattern Memory", "⊞", "Replay growing sequences of flashing cells.", "pattern")
        ]
        for i, (name, icon, desc, mode) in enumerate(modes):
            card = QWidget(); card.setObjectName("modeCard"); card.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            cl = QVBoxLayout(card); cl.setContentsMargins(0,0,0,0)
            ic = QLabel(f" {icon} "); ic.setObjectName("mcIcon"); ic.setAlignment(Qt.AlignmentFlag.AlignCenter); cl.addWidget(ic)
            n = QLabel(name); n.setObjectName("mcName"); cl.addWidget(n)
            d = QLabel(desc); d.setObjectName("mcDesc"); d.setWordWrap(True); cl.addWidget(d)
            best_val = self.settings.get(f"{mode}_best", 0)
            b_text = f"Best: {best_val/1000:.1f}s" if mode == "schulte" and best_val > 0 else (f"Best: {best_val} pts" if best_val > 0 else "")
            b = QLabel(b_text); b.setObjectName("mcBest"); cl.addWidget(b)
            card.mousePressEvent = lambda e, m=mode: self.start_mode(m)
            grid.addWidget(card, i // 4, i % 4)

        lay.addSpacing(20)
        stats = QLabel("Sessions <b>0</b>"); stats.setObjectName("statsBar"); stats.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(stats)
        return w

    # --- GAME & RESULTS SCREENS ---
    def create_game(self):
        w = QWidget(); lay = QVBoxLayout(w); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)
        header = QWidget(); header.setObjectName("gameHeader"); hl = QHBoxLayout(header); hl.setContentsMargins(16,8,16,8)
        self.back_btn = QPushButton("←"); self.back_btn.setObjectName("backBtn"); self.back_btn.clicked.connect(self.exit_game); hl.addWidget(self.back_btn)
        hl.addStretch(); self.game_title = QLabel(""); self.game_title.setObjectName("gameTitle"); hl.addWidget(self.game_title); hl.addStretch()
        self.round_disp = QLabel("<b>--</b>"); self.round_disp.setObjectName("statChip"); hl.addWidget(self.round_disp)
        self.score_disp = QLabel("<b>0</b>"); self.score_disp.setObjectName("statChip scoreChip"); hl.addWidget(self.score_disp)
        lay.addWidget(header)
        self.game_area = QWidget(); self.game_area_lay = QVBoxLayout(self.game_area); self.game_area_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.game_area, 1)
        self.game_footer = QLabel(""); self.game_footer.setObjectName("gameFooter"); self.game_footer.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(self.game_footer)
        return w

    def create_results(self):
        w = QWidget(); lay = QVBoxLayout(w); lay.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.setSpacing(12)
        self.res_title = QLabel(""); self.res_title.setObjectName("resTitle"); self.res_title.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(self.res_title)
        self.res_score = QLabel("0"); self.res_score.setObjectName("resScore"); self.res_score.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(self.res_score)
        self.res_label = QLabel("points"); self.res_label.setObjectName("resLabel"); self.res_label.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(self.res_label)
        self.res_best = QLabel(""); self.res_best.setObjectName("bestBadge"); self.res_best.setAlignment(Qt.AlignmentFlag.AlignCenter); self.res_best.hide(); lay.addWidget(self.res_best)
        self.res_metrics_lay = QGridLayout(); self.res_metrics_lay.setSpacing(12); lay.addLayout(self.res_metrics_lay)
        btn_lay = QHBoxLayout(); btn_lay.setSpacing(16); btn_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btn_again = QPushButton("Play Again"); self.btn_again.setObjectName("btnPrimary"); btn_lay.addWidget(self.btn_again)
        self.btn_hub = QPushButton("Back to Menu"); self.btn_hub.setObjectName("btnSecondary"); self.btn_hub.clicked.connect(self.go_to_hub); btn_lay.addWidget(self.btn_hub)
        lay.addLayout(btn_lay)
        return w

    def create_countdown(self):
        self.cd_widget = QWidget(self); self.cd_widget.setObjectName("countdownOverlay")
        self.cd_widget.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.cd_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground); self.cd_widget.hide()
        lay = QVBoxLayout(self.cd_widget); lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cd_text = QLabel("3"); self.cd_text.setObjectName("countdownText"); self.cd_text.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(self.cd_text)
        return self.cd_widget

    def show_countdown(self, callback):
        self.cd_widget.setGeometry(self.geometry()); self.cd_widget.show(); self.cd_widget.raise_()
        count = 3; self.cd_text.setText(str(count)); self.cd_text.setStyleSheet("color: #E8963A;")
        def tick():
            nonlocal count; count -= 1
            if count > 0: self.cd_text.setText(str(count)); self.sound.play("tick")
            elif count == 0: self.cd_text.setText("GO"); self.cd_text.setStyleSheet("color: #34D399;"); self.sound.play("go")
            else: self.cd_timer.stop(); self.cd_widget.hide(); self.cd_text.setStyleSheet("color: #E8963A;"); callback()
        self.cd_timer = QTimer(); self.cd_timer.timeout.connect(tick); self.timers.append(self.cd_timer); self.cd_timer.start(700)

    def set_header(self, title, round_text, score_text):
        self.game_title.setText(title); self.round_disp.setText(f"<b>{round_text}</b>"); self.score_disp.setText(f"<b>{score_text}</b>")
    def set_footer(self, text): self.game_footer.setText(text)

    def start_mode(self, mode):
        self.current_mode = mode; self.clear_layout(self.game_area_lay)
        self.set_header("", "--", "0"); self.set_footer(""); self.stack.setCurrentIndex(1)
        self.show_countdown(lambda: self._init_mode(mode))

    def _init_mode(self, mode):
        self.game_active = True
        if mode == "target": self.init_target()
        elif mode == "stroop": self.init_stroop()
        elif mode == "sequence": self.init_sequence()
        elif mode == "schulte": self.init_schulte()
        elif mode == "nback": self.init_nback()
        elif mode == "gonogo": self.init_gonogo()
        elif mode == "flanker": self.init_flanker()
        elif mode == "pattern": self.init_pattern()

    def exit_game(self):
        self.game_active = False; self.clear_timers(); self.clear_layout(self.game_area_lay)
        if hasattr(self, 'cd_timer'): self.cd_timer.stop()
        self.cd_widget.hide(); self.go_to_hub()

    def go_to_hub(self):
        self.clear_timers(); self.game_active = False; self.stack.setCurrentIndex(0)

    def show_results(self, data):
        self.game_active = False; self.sound.play("complete")
        prev_best = self.settings.get(f"{data['mode']}_best", 0)
        is_best = data['score'] > prev_best
        if is_best: self.settings[f"{data['mode']}_best"] = data['score']
        self.stack.setCurrentIndex(2)
        self.res_title.setText(data['title'])
        self.res_score.setText(str(data.get('display_score', data['score'])))
        self.res_label.setText(data.get('label', 'points'))
        self.res_best.setText("New Personal Best" if is_best else ""); self.res_best.setVisible(is_best)
        self.clear_layout(self.res_metrics_lay)
        for i, m in enumerate(data['metrics']):
            card = QWidget(); card.setObjectName("metricCard"); cl = QVBoxLayout(card)
            v = QLabel(m['value']); v.setObjectName("metricVal"); v.setAlignment(Qt.AlignmentFlag.AlignCenter); cl.addWidget(v)
            l = QLabel(m['label']); l.setObjectName("metricLabel"); l.setAlignment(Qt.AlignmentFlag.AlignCenter); cl.addWidget(l)
            self.res_metrics_lay.addWidget(card, i // 2, i % 2)
        try: self.btn_again.clicked.disconnect()
        except: pass
        self.btn_again.clicked.connect(lambda: self.start_mode(data['mode']))

    # ===================================================================
    # 1. TARGET SPOTTER
    # ===================================================================
    def init_target(self):
        self.t_state = {'round': 0, 'score': 0, 'hits': 0, 'total': 30, 'reactions': [], 'grid': 4, 'dur': 2000, 'active': False, 'ti': -1}
        self.build_target_grid(); self.target_next_round()

    def build_target_grid(self):
        self.clear_layout(self.game_area_lay); grid = QGridLayout(); grid.setSpacing(8); s = self.t_state; size = s['grid']
        container = QWidget(); container.setMaximumSize(400, 400); container.setLayout(grid); self.game_area_lay.addWidget(container)
        self.t_cells = []
        for i in range(size * size):
            btn = QPushButton(""); btn.setObjectName("targetCell"); btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            btn.clicked.connect(lambda checked, idx=i: self.target_click(idx))
            grid.addWidget(btn, i // size, i % size); self.t_cells.append(btn)

    def target_next_round(self):
        s = self.t_state
        if s['round'] >= s['total']: self.target_end(); return
        if s['round'] == 10: s['grid'] = 5; s['dur'] = 1500; self.build_target_grid()
        elif s['round'] == 20: s['dur'] = 1000
        s['round'] += 1; s['active'] = True; self.set_header("Target Spotter", f"{s['round']}/{s['total']}", s['score']); self.set_footer("Click the highlighted cell")
        for c in self.t_cells: c.setObjectName("targetCell"); c.setStyleSheet("")
        ti = random.randint(0, len(self.t_cells) - 1); s['ti'] = ti
        self.t_cells[ti].setObjectName("isTarget"); self.t_cells[ti].setStyleSheet("QPushButton { background-color: #E8963A; border: 1px solid #E8963A; border-radius: 10px; }")
        shadow = QGraphicsDropShadowEffect(); shadow.setColor(QColor(232, 150, 58, 150)); shadow.setBlurRadius(20); self.t_cells[ti].setGraphicsEffect(shadow)
        s['start_time'] = self.elapsed_ms()
        timer = QTimer(); timer.setSingleShot(True); timer.timeout.connect(self.target_timeout); timer.start(s['dur']); self.timers.append(timer)

    def target_click(self, idx):
        s = self.t_state
        if not s['active'] or not self.game_active: return
        s['active'] = False; self.clear_timers(); rt = self.elapsed_ms() - s['start_time']; cell = self.t_cells[idx]; cell.setGraphicsEffect(None)
        if idx == s['ti']:
            cell.setObjectName("isCorrect"); cell.setStyleSheet("QPushButton { background-color: #34D399; border: 1px solid #34D399; border-radius: 10px; }")
            s['hits'] += 1; s['reactions'].append(rt); s['score'] += 100 + max(0, int(100 - (rt / s['dur']) * 100)); self.sound.play("ok")
        else:
            cell.setObjectName("isWrong"); cell.setStyleSheet("QPushButton { background-color: #EF4444; border: 1px solid #EF4444; border-radius: 10px; }")
            self.t_cells[s['ti']].setGraphicsEffect(None); self.t_cells[s['ti']].setObjectName("isMissed"); self.t_cells[s['ti']].setStyleSheet("QPushButton { background-color: rgba(239,68,68,0.2); border: 1px solid rgba(239,68,68,0.5); border-radius: 10px; }")
            s['score'] = max(0, s['score'] - 50); self.sound.play("err")
        self.set_header("Target Spotter", f"{s['round']}/{s['total']}", s['score'])
        timer = QTimer(); timer.setSingleShot(True); timer.timeout.connect(self.target_next_round); timer.start(400); self.timers.append(timer)

    def target_timeout(self):
        s = self.t_state
        if not s['active'] or not self.game_active: return
        s['active'] = False; self.t_cells[s['ti']].setGraphicsEffect(None)
        self.t_cells[s['ti']].setObjectName("isMissed"); self.t_cells[s['ti']].setStyleSheet("QPushButton { background-color: rgba(239,68,68,0.2); border: 1px solid rgba(239,68,68,0.5); border-radius: 10px; }")
        s['score'] = max(0, s['score'] - 25); self.sound.play("err"); self.set_header("Target Spotter", f"{s['round']}/{s['total']}", s['score'])
        timer = QTimer(); timer.setSingleShot(True); timer.timeout.connect(self.target_next_round); timer.start(450); self.timers.append(timer)

    def target_end(self):
        s = self.t_state; avg = int(sum(s['reactions'])/len(s['reactions'])) if s['reactions'] else 0
        self.show_results({'mode': 'target', 'title': 'Target Spotter', 'score': s['score'], 'metrics': [
            {'value': f"{s['hits']}/{s['total']}", 'label': 'Hits'}, {'value': f"{avg}ms", 'label': 'Avg Reaction'},
            {'value': f"{min(s['reactions'])}ms" if s['reactions'] else "—", 'label': 'Best Reaction'},
            {'value': f"{int(s['hits']/s['total']*100)}%", 'label': 'Accuracy'}]})

    # ===================================================================
    # 2. STROOP CHALLENGE
    # ===================================================================
    STROOP_MAP = {"RED": "#E84A3A", "BLUE": "#4A8AE8", "GREEN": "#34D399", "YELLOW": "#E8D43A", "ORANGE": "#E88A3A", "PINK": "#E84A9A"}

    def init_stroop(self):
        self.s_state = {'round': 0, 'score': 0, 'hits': 0, 'total': 30, 'reactions': [], 'active': False}
        self.clear_layout(self.game_area_lay); lay = QVBoxLayout(); lay.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.setSpacing(40)
        self.s_word = QLabel("READY"); self.s_word.setObjectName("stroopWord"); self.s_word.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(self.s_word)
        opts_lay = QGridLayout(); opts_lay.setSpacing(12); self.s_opts = []
        for i in range(4):
            btn = QPushButton(""); btn.setObjectName("stroopBtn"); btn.setMinimumSize(140, 60); btn.clicked.connect(lambda checked, idx=i: self.stroop_click(idx))
            opts_lay.addWidget(btn, i // 2, i % 2); self.s_opts.append(btn)
        lay.addLayout(opts_lay); self.game_area_lay.addLayout(lay); self.stroop_next_round()

    def stroop_next_round(self):
        s = self.s_state
        if s['round'] >= s['total']: self.stroop_end(); return
        s['round'] += 1; s['active'] = True; self.set_header("Stroop Challenge", f"{s['round']}/{s['total']}", s['score']); self.set_footer("Click the COLOR the text is displayed in")
        names = list(self.STROOP_MAP.keys()); word = random.choice(names); display_color_name = random.choice([n for n in names if n != word])
        options = [display_color_name] + random.sample([n for n in names if n != display_color_name], 3); random.shuffle(options)
        self.s_word.setText(word); self.s_word.setStyleSheet(f"color: {self.STROOP_MAP[display_color_name]}; font-size: 72px; font-weight: 800;")
        s['ci'] = options.index(display_color_name)
        for i, btn in enumerate(self.s_opts): btn.setText(options[i]); btn.setStyleSheet(f"background-color: {self.STROOP_MAP[options[i]]}; border: 2px solid transparent; border-radius: 11px; padding: 16px; font-weight: 700; font-size: 16px; color: #000;")
        s['start_time'] = self.elapsed_ms()

    def stroop_click(self, idx):
        s = self.s_state
        if not s['active'] or not self.game_active: return
        s['active'] = False; rt = self.elapsed_ms() - s['start_time']
        if idx == s['ci']:
            self.s_opts[idx].setStyleSheet(self.s_opts[idx].styleSheet().replace("transparent", "#34D399")); s['hits'] += 1; s['reactions'].append(rt); s['score'] += 100 + max(0, int(100 - (rt / 3000) * 100)); self.sound.play("ok")
        else:
            self.s_opts[idx].setStyleSheet(self.s_opts[idx].styleSheet().replace("transparent", "#EF4444"))
            self.s_opts[s['ci']].setStyleSheet(self.s_opts[s['ci']].styleSheet().replace("transparent", "#34D399")); s['score'] = max(0, s['score'] - 50); self.sound.play("err")
        self.set_header("Stroop Challenge", f"{s['round']}/{s['total']}", s['score'])
        timer = QTimer(); timer.setSingleShot(True); timer.timeout.connect(self.stroop_next_round); timer.start(550); self.timers.append(timer)

    def stroop_end(self):
        s = self.s_state; avg = int(sum(s['reactions'])/len(s['reactions'])) if s['reactions'] else 0
        self.show_results({'mode': 'stroop', 'title': 'Stroop Challenge', 'score': s['score'], 'metrics': [
            {'value': f"{s['hits']}/{s['total']}", 'label': 'Correct'}, {'value': f"{avg}ms", 'label': 'Avg Reaction'}, {'value': f"{int(s['hits']/s['total']*100)}%", 'label': 'Accuracy'}]})

    # ===================================================================
    # 3. NUMBER SEQUENCE
    # ===================================================================
    def init_sequence(self):
        self.n_state = {'level': 3, 'score': 0, 'phase': 'showing', 'seq': [], 'input': [], 'show_idx': 0, 'cleared': 0}
        self.clear_layout(self.game_area_lay); lay = QVBoxLayout(); lay.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.setSpacing(24)
        self.n_display = QLabel("?"); self.n_display.setObjectName("seqDisplay"); self.n_display.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(self.n_display)
        self.n_input_widget = QWidget(); self.n_input_lay = QVBoxLayout(self.n_input_widget); self.n_input_lay.setAlignment(Qt.AlignmentFlag.AlignCenter); self.n_input_lay.setSpacing(16); self.n_input_widget.hide(); lay.addWidget(self.n_input_widget)
        self.n_prog_lay = QHBoxLayout(); self.n_prog_lay.setAlignment(Qt.AlignmentFlag.AlignCenter); self.n_prog_lay.setSpacing(8); self.n_input_lay.addLayout(self.n_prog_lay); self.n_digits = []
        pad_grid = QGridLayout(); pad_grid.setSpacing(8)
        for i in range(9): btn = QPushButton(str(i+1)); btn.setObjectName("numBtn"); btn.clicked.connect(lambda checked, n=i+1: self.seq_digit(n)); pad_grid.addWidget(btn, i//3, i%3)
        bs = QPushButton("⌫"); bs.setObjectName("numBtn action"); bs.clicked.connect(self.seq_bs); pad_grid.addWidget(bs, 3, 0)
        z = QPushButton("0"); z.setObjectName("numBtn"); z.clicked.connect(lambda checked: self.seq_digit(0)); pad_grid.addWidget(z, 3, 1)
        ok = QPushButton("✓"); ok.setObjectName("numBtn action"); ok.setStyleSheet("color: #34D399;"); ok.clicked.connect(self.seq_submit); pad_grid.addWidget(ok, 3, 2)
        self.n_input_lay.addLayout(pad_grid); self.game_area_lay.addLayout(lay); self.seq_gen(); self.seq_show_next()

    def seq_gen(self): self.n_state['seq'] = [random.randint(0, 9) for _ in range(self.n_state['level'])]; self.n_state['input'] = []

    def seq_show_next(self):
        s = self.n_state
        if s['show_idx'] >= len(s['seq']): s['phase'] = 'input'; self.n_display.hide(); self.n_input_widget.show(); self.seq_render_prog(); self.set_footer("Enter the sequence"); return
        self.n_display.show(); self.n_display.setText(str(s['seq'][s['show_idx']])); self.set_header("Number Sequence", f"Level {s['level']}", str(s['score'])); self.set_footer(f"{s['show_idx'] + 1} of {len(s['seq'])}")
        s['show_idx'] += 1
        timer = QTimer(); timer.setSingleShot(True); timer.timeout.connect(self.seq_show_gap); timer.start(800); self.timers.append(timer)

    def seq_show_gap(self):
        self.n_display.setText("")
        timer = QTimer(); timer.setSingleShot(True); timer.timeout.connect(self.seq_show_next); timer.start(200); self.timers.append(timer)

    def seq_render_prog(self):
        for d in self.n_digits: d.deleteLater()
        self.n_digits.clear()
        for i, val in enumerate(self.n_state['input']): lbl = QPushButton(str(val)); lbl.setObjectName("seqDigit filled"); lbl.setEnabled(False); self.n_prog_lay.addWidget(lbl); self.n_digits.append(lbl)
        for i in range(len(self.n_state['input']), len(self.n_state['seq'])): lbl = QPushButton(""); lbl.setObjectName("seqDigit"); lbl.setEnabled(False); self.n_prog_lay.addWidget(lbl); self.n_digits.append(lbl)

    def seq_digit(self, n):
        s = self.n_state
        if s['phase'] != 'input' or not self.game_active or len(s['input']) >= len(s['seq']): return
        s['input'].append(n); self.sound.play("tick"); self.seq_render_prog()
        if len(s['input']) == len(s['seq']): timer = QTimer(); timer.setSingleShot(True); timer.timeout.connect(self.seq_submit); timer.start(200); self.timers.append(timer)

    def seq_bs(self):
        if self.n_state['phase'] != 'input' or not self.game_active: return
        if self.n_state['input']: self.n_state['input'].pop()
        self.seq_render_prog()

    def seq_submit(self):
        s = self.n_state
        if s['phase'] != 'input' or not self.game_active: return
        s['phase'] = 'feedback'; correct = True; wrong_idx = -1
        for i in range(len(s['seq'])):
            if i >= len(s['input']) or s['input'][i] != s['seq'][i]: correct = False; wrong_idx = i; break
        if correct:
            for d in self.n_digits: d.setObjectName("seqDigit correct"); d.setStyleSheet("")
            s['score'] += s['level']; s['cleared'] += 1; self.sound.play("ok"); self.set_header("Number Sequence", f"Level {s['level']}", str(s['score']))
            timer = QTimer(); timer.setSingleShot(True); timer.timeout.connect(self.seq_next_level); timer.start(1100); self.timers.append(timer)
        else:
            for i, d in enumerate(self.n_digits):
                d.setStyleSheet("")
                if i == wrong_idx: d.setObjectName("seqDigit wrong"); d.setText(s['input'][i] if i<len(s['input']) else "")
                elif i < len(s['input']): d.setObjectName("seqDigit correct"); d.setText(s['input'][i])
            self.sound.play("err"); timer = QTimer(); timer.setSingleShot(True); timer.timeout.connect(self.seq_end); timer.start(2000); self.timers.append(timer)

    def seq_next_level(self):
        self.n_state['level'] += 1; self.n_state['phase'] = 'showing'; self.n_state['show_idx'] = 0; self.n_input_widget.hide(); self.seq_gen(); self.seq_show_next()

    def seq_end(self):
        s = self.n_state
        self.show_results({'mode': 'sequence', 'title': 'Number Sequence', 'score': s['score'], 'metrics': [
            {'value': f"Level {s['level']}", 'label': 'Reached'}, {'value': str(s['cleared']), 'label': 'Levels Cleared'}, {'value': str(s['score']), 'label': 'Total Recalled'}]})

    # ===================================================================
    # 4. SCHULTE TABLE
    # ===================================================================
    def init_schulte(self):
        self.sc_state = {'next_num': 1, 'total': 25, 'active': True, 'errors': 0}
        self.clear_layout(self.game_area_lay); grid = QGridLayout(); grid.setSpacing(6)
        container = QWidget(); container.setMaximumSize(450, 450); container.setLayout(grid); self.game_area_lay.addWidget(container)
        nums = list(range(1, 26)); random.shuffle(nums); self.sc_cells = []
        for i, n in enumerate(nums):
            btn = QPushButton(str(n)); btn.setObjectName("schulteCell"); btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            btn.clicked.connect(lambda checked, num=n: self.sc_click(num)); grid.addWidget(btn, i // 5, i % 5); self.sc_cells.append(btn)
        self.set_header("Schulte Table", "Find 1-25", "0"); self.set_footer("Find and click numbers 1 through 25 in order")
        self.start_time = self.elapsed_ms()
        self.sc_timer = QTimer(); self.sc_timer.timeout.connect(self.sc_update_time); self.sc_timer.start(100); self.timers.append(self.sc_timer)

    def sc_update_time(self):
        if not self.game_active: return
        self.round_disp.setText(f"<b>{(self.elapsed_ms() - self.start_time) / 1000.0:.1f}s</b>")

    def sc_click(self, num):
        s = self.sc_state
        if not s['active'] or not self.game_active: return
        if num == s['next_num']:
            self.sc_cells[num-1].setObjectName("schulteCell found"); self.sc_cells[num-1].setStyleSheet(""); self.sc_cells[num-1].setEnabled(False)
            s['next_num'] += 1; self.sound.play("tick")
            if s['next_num'] > s['total']: self.sc_end()
        else:
            self.sc_cells[num-1].setObjectName("schulteCell wrong"); self.sc_cells[num-1].setStyleSheet(""); s['errors'] += 1; self.sound.play("err")
            timer = QTimer(); timer.setSingleShot(True); timer.timeout.connect(lambda n=num: self.sc_reset_cell(n)); timer.start(300); self.timers.append(timer)

    def sc_reset_cell(self, num):
        if self.sc_cells[num-1].objectName() == "schulteCell wrong": self.sc_cells[num-1].setObjectName("schulteCell"); self.sc_cells[num-1].setStyleSheet("")

    def sc_end(self):
        self.sc_state['active'] = False; self.sc_timer.stop()
        elapsed = (self.elapsed_ms() - self.start_time) / 1000.0
        score = max(0, int(3000 - elapsed * 20) - (self.sc_state['errors'] * 100))
        self.show_results({'mode': 'schulte', 'title': 'Schulte Table', 'score': score, 'display_score': f"{elapsed:.1f}s", 'label': 'time', 'metrics': [
            {'value': f"{elapsed:.1f}s", 'label': 'Total Time'}, {'value': str(self.sc_state['errors']), 'label': 'Missclicks'}, {'value': f"{elapsed/25:.2f}s", 'label': 'Avg Per Num'}]})

    # ===================================================================
    # 5. N-BACK
    # ===================================================================
    def init_nback(self):
        self.nb_state = {'round': 0, 'total': 22, 'n': 2, 'score': 0, 'hits': 0, 'false_alarms': 0, 'misses': 0, 'seq': [], 'active': False, 'answered': False}
        self.clear_layout(self.game_area_lay); lay = QVBoxLayout(); lay.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.setSpacing(30)
        grid = QGridLayout(); grid.setSpacing(8); self.nb_cells = []
        for i in range(9):
            btn = QPushButton(""); btn.setObjectName("nbackCell"); btn.setFixedSize(80, 80); btn.setEnabled(False)
            grid.addWidget(btn, i // 3, i % 3); self.nb_cells.append(btn)
        lay.addLayout(grid)
        btn_lay = QHBoxLayout(); btn_lay.setSpacing(20)
        self.nb_match_btn = QPushButton("Match"); self.nb_match_btn.setObjectName("nbackBtn match"); self.nb_match_btn.clicked.connect(lambda: self.nb_answer(True)); btn_lay.addWidget(self.nb_match_btn)
        self.nb_diff_btn = QPushButton("Different"); self.nb_diff_btn.setObjectName("nbackBtn"); self.nb_diff_btn.clicked.connect(lambda: self.nb_answer(False)); btn_lay.addWidget(self.nb_diff_btn)
        lay.addLayout(btn_lay); self.game_area_lay.addLayout(lay)
        self.nb_state['seq'] = [random.randint(0, 8) for _ in range(self.nb_state['total'])]
        for i in range(self.nb_state['n'], self.nb_state['total']):
            if random.random() < 0.35: self.nb_state['seq'][i] = self.nb_state['seq'][i - self.nb_state['n']]
        self.set_header("N-Back (2)", "0 / 22", "0"); self.set_footer("Does current position match 2 steps back?"); self.nb_next_round()

    def nb_next_round(self):
        s = self.nb_state
        if s['round'] >= s['total']: self.nb_end(); return
        s['round'] += 1; s['active'] = True; s['answered'] = False
        self.set_header(f"N-Back ({s['n']})", f"{s['round']} / {s['total']}", str(s['score']))
        for c in self.nb_cells: c.setObjectName("nbackCell"); c.setStyleSheet("")
        if s['round'] > 2: self.nb_cells[s['seq'][s['round']-3]].setObjectName("nbackCell"); self.nb_cells[s['seq'][s['round']-3]].setStyleSheet("")
        if s['round'] > 1: self.nb_cells[s['seq'][s['round']-2]].setObjectName("nbackCell history"); self.nb_cells[s['seq'][s['round']-2]].setStyleSheet("QWidget { background-color: rgba(232,150,58,0.15); border: 2px solid rgba(232,150,58,0.4); border-radius: 10px; }")
        curr = s['seq'][s['round']-1]
        self.nb_cells[curr].setObjectName("nbackCell active"); self.nb_cells[curr].setStyleSheet("QWidget { background-color: #E8963A; border: 2px solid #E8963A; border-radius: 10px; }")
        timer = QTimer(); timer.setSingleShot(True); timer.timeout.connect(self.nb_timeout); timer.start(2500); self.timers.append(timer)

    def nb_answer(self, is_match):
        s = self.nb_state
        if not s['active'] or s['answered'] or not self.game_active: return
        s['answered'] = True; s['active'] = False; self.clear_timers()
        actual_match = (s['round'] > s['n']) and (s['seq'][s['round']-1] == s['seq'][s['round']-1 - s['n']])
        if is_match == actual_match:
            if is_match: s['hits'] += 1; s['score'] += 100
            else: s['score'] += 25
            self.sound.play("ok")
        else:
            if is_match: s['false_alarms'] += 1; s['score'] = max(0, s['score'] - 50)
            else: s['misses'] += 1; s['score'] = max(0, s['score'] - 25)
            self.sound.play("err")
        self.set_header(f"N-Back ({s['n']})", f"{s['round']} / {s['total']}", str(s['score']))
        timer = QTimer(); timer.setSingleShot(True); timer.timeout.connect(self.nb_next_round); timer.start(500); self.timers.append(timer)

    def nb_timeout(self):
        s = self.nb_state
        if not s['active'] or not self.game_active: return
        if not s['answered']:
            actual_match = (s['round'] > s['n']) and (s['seq'][s['round']-1] == s['seq'][s['round']-1 - s['n']])
            if actual_match: s['misses'] += 1; s['score'] = max(0, s['score'] - 25)
            else: s['score'] += 25
        s['active'] = False
        timer = QTimer(); timer.setSingleShot(True); timer.timeout.connect(self.nb_next_round); timer.start(300); self.timers.append(timer)

    def nb_end(self):
        s = self.nb_state
        self.show_results({'mode': 'nback', 'title': 'N-Back Memory', 'score': s['score'], 'metrics': [
            {'value': str(s['hits']), 'label': 'True Hits'}, {'value': str(s['false_alarms']), 'label': 'False Alarms'}, {'value': str(s['misses']), 'label': 'Misses'}]})

    # ===================================================================
    # 6. GO / NO-GO
    # ===================================================================
    def init_gonogo(self):
        self.gng_state = {'round': 0, 'total': 30, 'score': 0, 'hits': 0, 'misses': 0, 'false_alarms': 0, 'rts': [], 'active': False, 'is_no_go': False}
        self.clear_layout(self.game_area_lay); lay = QVBoxLayout(); lay.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.setSpacing(20)
        self.gng_letter = QLabel(""); self.gng_letter.setObjectName("gonogoLetter"); self.gng_letter.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(self.gng_letter)
        self.gng_feedback = QLabel(""); self.gng_feedback.setObjectName("gonogoFeedback"); self.gng_feedback.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(self.gng_feedback)
        self.game_area_lay.addLayout(lay); self.set_header("Go / No-Go", "0 / 30", "0"); self.set_footer("Press SPACE for letters, do NOTHING for X")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus); self.setFocus(); self.gng_next_round()

    def gng_next_round(self):
        s = self.gng_state
        if s['round'] >= s['total']: self.gng_end(); return
        s['round'] += 1; s['active'] = True; self.set_header("Go / No-Go", f"{s['round']} / {s['total']}", str(s['score'])); self.gng_feedback.setText("")
        s['is_no_go'] = random.random() < 0.25
        letter = "X" if s['is_no_go'] else random.choice([c for c in "ABCDEFGHJKLMNPQRSTUVWZ"])
        color = "#EF4444" if s['is_no_go'] else "#F0ECE3"
        self.gng_letter.setText(letter); self.gng_letter.setStyleSheet(f"color: {color}; font-size: 160px; font-weight: 800; font-family: 'Courier New', monospace;")
        timer = QTimer(); timer.setSingleShot(True); timer.timeout.connect(self.gng_timeout); timer.start(1500); self.timers.append(timer)

    def gng_handle_input(self):
        s = self.gng_state
        if not s['active'] or not self.game_active: return
        s['active'] = False; self.clear_timers(); rt = self.elapsed_ms() - s['start_time']
        if s['is_no_go']:
            s['false_alarms'] += 1; s['score'] = max(0, s['score'] - 50); self.gng_feedback.setText("FALSE ALARM"); self.gng_feedback.setStyleSheet("color: #EF4444; font-size: 24px; font-weight: 700;"); self.sound.play("err")
        else:
            s['hits'] += 1; s['rts'].append(rt); s['score'] += 50 + max(0, int(100 - (rt / 1000) * 100)); self.gng_feedback.setText(f"GO! ({rt}ms)"); self.gng_feedback.setStyleSheet("color: #34D399; font-size: 24px; font-weight: 700;"); self.sound.play("ok")
        self.set_header("Go / No-Go", f"{s['round']} / {s['total']}", str(s['score']))
        timer = QTimer(); timer.setSingleShot(True); timer.timeout.connect(self.gng_next_round); timer.start(800); self.timers.append(timer)

    def gng_timeout(self):
        s = self.gng_state
        if not s['active'] or not self.game_active: return
        s['active'] = False
        if not s['is_no_go']:
            s['misses'] += 1; s['score'] = max(0, s['score'] - 25); self.gng_feedback.setText("MISSED"); self.gng_feedback.setStyleSheet("color: #E8963A; font-size: 24px; font-weight: 700;"); self.sound.play("err")
        else:
            self.gng_feedback.setText("CORRECT REJECTION"); self.gng_feedback.setStyleSheet("color: #34D399; font-size: 24px; font-weight: 700;"); s['score'] += 20
        self.set_header("Go / No-Go", f"{s['round']} / {s['total']}", str(s['score']))
        timer = QTimer(); timer.setSingleShot(True); timer.timeout.connect(self.gng_next_round); timer.start(800); self.timers.append(timer)

    def gng_end(self):
        s = self.gng_state; avg = int(sum(s['rts'])/len(s['rts'])) if s['rts'] else 0
        self.show_results({'mode': 'gonogo', 'title': 'Go / No-Go', 'score': s['score'], 'metrics': [
            {'value': str(s['hits']), 'label': 'Hits'}, {'value': str(s['false_alarms']), 'label': 'False Alarms'}, {'value': f"{avg}ms", 'label': 'Avg Reaction'}]})

    # ===================================================================
    # 7. FLANKER TASK
    # ===================================================================
    def init_flanker(self):
        self.fk_state = {'round': 0, 'total': 30, 'score': 0, 'hits': 0, 'errors': 0, 'rts': [], 'active': False, 'target_dir': 'L'}
        self.clear_layout(self.game_area_lay); lay = QVBoxLayout(); lay.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.setSpacing(40)
        self.fk_arrows = QLabel("← ← ← ← ←"); self.fk_arrows.setObjectName("flankerArrows"); self.fk_arrows.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(self.fk_arrows)
        self.fk_feedback = QLabel(""); self.fk_feedback.setObjectName("flankerFeedback"); self.fk_feedback.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(self.fk_feedback)
        btn_lay = QHBoxLayout(); btn_lay.setSpacing(40)
        btn_l = QPushButton("← LEFT"); btn_l.setObjectName("flankerBtn"); btn_l.clicked.connect(lambda: self.flanker_answer('L')); btn_lay.addWidget(btn_l)
        btn_r = QPushButton("RIGHT →"); btn_r.setObjectName("flankerBtn"); btn_r.clicked.connect(lambda: self.flanker_answer('R')); btn_lay.addWidget(btn_r)
        lay.addLayout(btn_lay); self.game_area_lay.addLayout(lay)
        self.set_header("Flanker Task", "0 / 30", "0"); self.set_footer("Identify the CENTER arrow. Use buttons or Arrow Keys.")
        self.flanker_next_round()

    def flanker_next_round(self):
        s = self.fk_state
        if s['round'] >= s['total']: self.flanker_end(); return
        s['round'] += 1; s['active'] = True; self.set_header("Flanker Task", f"{s['round']} / {s['total']}", str(s['score']))
        self.fk_feedback.setText("")
        target = random.choice(['←', '→'])
        s['target_dir'] = 'L' if target == '←' else 'R'
        congruent = random.random() < 0.5
        flanker = target if congruent else ('→' if target == '←' else '←')
        text = f"{flanker} {flanker} {target} {flanker} {flanker}"
        self.fk_arrows.setText(text)
        color = "#F0ECE3" if congruent else "#E8963A"
        self.fk_arrows.setStyleSheet(f"font-size: 100px; font-weight: 800; font-family: 'Courier New', monospace; letter-spacing: 8px; color: {color};")
        s['start_time'] = self.elapsed_ms()
        timer = QTimer(); timer.setSingleShot(True); timer.timeout.connect(self.flanker_timeout); timer.start(2000); self.timers.append(timer)

    def flanker_answer(self, direction):
        s = self.fk_state
        if not s['active'] or not self.game_active: return
        s['active'] = False; self.clear_timers(); rt = self.elapsed_ms() - s['start_time']
        if direction == s['target_dir']:
            s['hits'] += 1; s['rts'].append(rt); s['score'] += 50 + max(0, int(50 - (rt / 1000) * 50))
            self.fk_feedback.setText(f"CORRECT ({rt}ms)"); self.fk_feedback.setStyleSheet("color: #34D399;"); self.sound.play("ok")
        else:
            s['errors'] += 1; s['score'] = max(0, s['score'] - 25)
            self.fk_feedback.setText("WRONG"); self.fk_feedback.setStyleSheet("color: #EF4444;"); self.sound.play("err")
        self.set_header("Flanker Task", f"{s['round']} / {s['total']}", str(s['score']))
        timer = QTimer(); timer.setSingleShot(True); timer.timeout.connect(self.flanker_next_round); timer.start(600); self.timers.append(timer)

    def flanker_timeout(self):
        s = self.fk_state
        if not s['active'] or not self.game_active: return
        s['active'] = False; s['errors'] += 1; s['score'] = max(0, s['score'] - 25)
        self.fk_feedback.setText("TOO SLOW"); self.fk_feedback.setStyleSheet("color: #E8963A;"); self.sound.play("err")
        self.set_header("Flanker Task", f"{s['round']} / {s['total']}", str(s['score']))
        timer = QTimer(); timer.setSingleShot(True); timer.timeout.connect(self.flanker_next_round); timer.start(600); self.timers.append(timer)

    def flanker_end(self):
        s = self.fk_state; avg = int(sum(s['rts'])/len(s['rts'])) if s['rts'] else 0
        self.show_results({'mode': 'flanker', 'title': 'Flanker Task', 'score': s['score'], 'metrics': [
            {'value': f"{s['hits']}/{s['total']}", 'label': 'Accuracy'}, {'value': f"{avg}ms", 'label': 'Avg Reaction'},
            {'value': str(s['errors']), 'label': 'Errors/Misses'}, {'value': str(s['score']), 'label': 'Score'}]})

    # ===================================================================
    # 8. PATTERN MEMORY
    # ===================================================================
    def init_pattern(self):
        self.pm_state = {'level': 3, 'score': 0, 'phase': 'showing', 'seq': [], 'input': [], 'show_idx': 0, 'cleared': 0}
        self.clear_layout(self.game_area_lay)
        grid = QGridLayout(); grid.setSpacing(8)
        container = QWidget(); container.setMaximumSize(320, 320); container.setLayout(grid); self.game_area_lay.addWidget(container)
        self.pm_cells = []
        for i in range(16):
            btn = QPushButton(""); btn.setObjectName("patternCell"); btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            btn.clicked.connect(lambda checked, idx=i: self.pm_click(idx))
            grid.addWidget(btn, i // 4, i % 4); self.pm_cells.append(btn)
        self.set_header("Pattern Memory", "Level 3", "0"); self.set_footer("Watch the pattern...")
        self.pm_gen(); self.pm_show_next()

    def pm_gen(self): self.pm_state['seq'] = [random.randint(0, 15) for _ in range(self.pm_state['level'])]; self.pm_state['input'] = []

    def pm_show_next(self):
        s = self.pm_state
        for c in self.pm_cells: c.setObjectName("patternCell"); c.setStyleSheet("")
        if s['show_idx'] >= len(s['seq']):
            s['phase'] = 'input'; self.set_footer("Reproduce the pattern"); return
        self.pm_cells[s['seq'][s['show_idx]]].setObjectName("patternCell active")
        self.pm_cells[s['seq'][s['show_idx]]].setStyleSheet("QWidget { background-color: #E8963A; border: 2px solid #E8963A; border-radius: 10px; }")
        s['show_idx'] += 1
        timer = QTimer(); timer.setSingleShot(True); timer.timeout.connect(self.pm_gap); timer.start(500); self.timers.append(timer)

    def pm_gap(self):
        for c in self.pm_cells: c.setObjectName("patternCell"); c.setStyleSheet("")
        timer = QTimer(); timer.setSingleShot(True); timer.timeout.connect(self.pm_show_next); timer.start(200); self.timers.append(timer)

    def pm_click(self, idx):
        s = self.pm_state
        if s['phase'] != 'input' or not self.game_active: return
        if idx == s['seq'][len(s['input'])]:
            s['input'].append(idx); self.sound.play("tick")
            self.pm_cells[idx].setObjectName("patternCell found"); self.pm_cells[idx].setStyleSheet("QWidget { background-color: rgba(52,211,153,0.2); border: 2px solid #34D399; border-radius: 10px; }")
            if len(s['input']) == len(s['seq']):
                s['score'] += s['level']; s['cleared'] += 1; self.sound.play("ok")
                self.set_header("Pattern Memory", f"Level {s['level']}", str(s['score']))
                timer = QTimer(); timer.setSingleShot(True); timer.timeout.connect(self.pm_next_level); timer.start(1000); self.timers.append(timer)
        else:
            self.pm_cells[idx].setObjectName("patternCell wrong"); self.pm_cells[idx].setStyleSheet("QWidget { background-color: rgba(239,68,68,0.2); border: 2px solid #EF4444; border-radius: 10px; }")
            self.sound.play("err")
            timer = QTimer(); timer.setSingleShot(True); timer.timeout.connect(self.pm_end); timer.start(1500); self.timers.append(timer)

    def pm_next_level(self):
        self.pm_state['level'] += 1; self.pm_state['phase'] = 'showing'; self.pm_state['show_idx'] = 0
        self.set_header("Pattern Memory", f"Level {self.pm_state['level']}", str(self.pm_state['score']))
        self.set_footer("Watch the pattern...")
        self.pm_gen(); self.pm_show_next()

    def pm_end(self):
        s = self.pm_state
        self.show_results({'mode': 'pattern', 'title': 'Pattern Memory', 'score': s['score'], 'metrics': [
            {'value': f"Level {s['level']}", 'label': 'Reached'}, {'value': str(s['cleared']), 'label': 'Patterns Cleared'},
            {'value': str(s['score']), 'label': 'Score'}, {'value': f"Length {s['level']}", 'label': 'Final Sequence'}]})

    # --- Keyboard Events ---
    def keyPressEvent(self, event):
        if not self.game_active: return super().keyPressEvent(event)
        if event.key() == Qt.Key.Key_Space:
            if self.current_mode == 'gonogo': self.gng_handle_input()
        elif event.key() == Qt.Key.Key_Left:
            if self.current_mode == 'flanker': self.flanker_answer('L')
        elif event.key() == Qt.Key.Key_Right:
            if self.current_mode == 'flanker': self.flanker_answer('R')
        elif event.key() == Qt.Key.Key_Escape: self.exit_game()
        else: super().keyPressEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    window = FocusTrainer()
    window.show()
    sys.exit(app.exec())