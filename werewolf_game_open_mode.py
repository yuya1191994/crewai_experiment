# CrewAI人狼ゲーム - 10人村
import os
import random
import datetime
from crewai import Agent, Task, Crew, LLM

# --------------------------------------------------------------------
# 1. LLM（大規模言語モデル）のセットアップ
# --------------------------------------------------------------------
def setup_llm():
    """Gemini LLMを初期化（CrewAI 0.134.0版）"""
    try:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY環境変数が設定されていません")
        
        llm = LLM(
            model="gemini/gemini-2.5-flash",
            api_key=api_key,
            temperature=0.8  # 人狼ゲームは創造性が重要なので高めに設定
        )
        print("✅ LLM初期化成功")
        return llm
    except Exception as e:
        print(f"❌ LLM初期化エラー: {e}")
        exit(1)

# --------------------------------------------------------------------
# 2. ログ管理クラス
# --------------------------------------------------------------------
class WerewolfLogger:
    def __init__(self):
        # warewolf_logs ディレクトリを作成（既存でもエラーなし）
        os.makedirs("warewolf_logs", exist_ok=True)
        
        # タイムスタンプでログファイル名を生成（最新順で並ぶ）
        timestamp = datetime.datetime.now()
        timestamp_str = timestamp.strftime("%Y%m%d%H%M%S")
        self.log_file = f"warewolf_logs/open_mode_{timestamp_str}.md"
        
        # ログファイルを初期化
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(f"🐺 CrewAI人狼ゲーム ログ - {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
        
        print(f"📝 ログファイル作成: {self.log_file}")
    
    def log_and_print(self, message):
        """メッセージをコンソールに表示し、ログファイルにも記録"""
        print(message)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(message + "\n")
    
    def log_phase(self, phase_name, day_num=None):
        """フェーズの開始をログ"""
        if day_num:
            msg = f"\n{'='*60}\n{phase_name} - {day_num}日目\n{'='*60}"
        else:
            msg = f"\n{'='*60}\n{phase_name}\n{'='*60}"
        self.log_and_print(msg)
    
    def log_result(self, result, title=""):
        """CrewAIの実行結果をログ"""
        self.log_and_print(f"\n--- {title} ---")
        self.log_and_print(str(result))

# --------------------------------------------------------------------
# 3. ゲーム状態管理クラス
# --------------------------------------------------------------------
class WerewolfGameState:
    def __init__(self):
        self.day_count = 0
        self.phase = "night"  # "day" or "night"
        self.alive_players = []
        self.dead_players = []
        self.votes = {}
        self.night_actions = {}
        self.game_over = False
        self.winner = None
        
        # 役職別リスト
        self.werewolves = ['werewolf1', 'werewolf2']
        self.madman = 'madman'
        self.fortune_teller = 'fortune_teller'
        self.knight = 'knight'
        self.citizens = ['citizen1', 'citizen2', 'citizen3', 'citizen4']
        
        # 占い・護衛結果
        self.fortune_results = []
        self.protected_player = None

# --------------------------------------------------------------------
# 3. 各役職のエージェント作成
# --------------------------------------------------------------------
def create_werewolf_agents(llm):
    """人狼ゲームの各プレイヤーエージェントを作成"""
    
    # ゲームマスター
    game_master = Agent(
        role='ゲームマスター',
        goal='公正で白熱した人狼ゲームを進行し、プレイヤーたちの推理と駆け引きを最大限に引き出す',
        backstory="""あなたは数百回の人狼ゲームを進行してきたベテランゲームマスターです。
        プレイヤーの心理を読み、適切なタイミングで情報を開示し、ゲームを盛り上げることに長けています。
        中立的な立場を保ちながら、全プレイヤーが楽しめるよう配慮します。
        
        ★重要★ 必ず日本語のみで発言してください。英語や他の言語は一切使用禁止です。""",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
    
    # 人狼1（リーダータイプ）
    werewolf1 = Agent(
        role='人狼（アルファ）',
        goal='仲間の人狼と連携し、市民を騙して人狼陣営の勝利を目指す',
        backstory="""あなたは冷静沈着で戦略的思考に優れた人狼です。人狼歴3年のベテランで、
        リーダーシップを発揮して仲間を導きます。論理的な推理で市民を装い、
        巧妙な誘導で村人同士を疑心暗鬼に陥れることを得意とします。
        仲間の人狼との連携を重視し、夜の作戦会議では積極的に戦略を提案します。
        
        ★重要★ 必ず日本語のみで発言してください。英語や他の言語は一切使用禁止です。""",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
    
    # 人狼2（演技派タイプ）
    werewolf2 = Agent(
        role='人狼（カメレオン）',
        goal='優れた演技力で市民を騙し、人狼陣営の勝利に貢献する',
        backstory="""あなたは卓越した演技力を持つ人狼です。感情豊かで表現力があり、
        時には涙を流しながら無実を訴えることもできます。人狼歴2年で、
        特に市民になりきる演技が得意です。相手の感情に訴えかける話術と、
        絶妙なタイミングでの情報開示で場をコントロールします。
        仲間との連携では、アルファの戦略を巧みに実行する役割を担います。
        
        ★重要★ 必ず日本語のみで発言してください。英語や他の言語は一切使用禁止です。""",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
    
    # 狂人
    madman = Agent(
        role='狂人',
        goal='人狼陣営の勝利のために村を混乱させ、偽情報を流して市民を惑わす',
        backstory="""あなたは人狼陣営に属する狂人です。人狼の正体は知らないものの、
        人狼勝利のために働く特殊な役職です。人狼ゲーム歴4年のエキスパートで、
        大胆で予測不可能な行動を取ります。偽占い師COや突飛な推理で場を荒らし、
        市民の推理を混乱させることに喜びを感じます。時には自分が疑われるリスクも
        厭わず、村全体を巻き込む大胆な戦略を実行します。
        
        ★重要★ 必ず日本語のみで発言してください。英語や他の言語は一切使用禁止です。""",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
    
    # 占い師
    fortune_teller = Agent(
        role='占い師',
        goal='人狼を見つけ出し、市民陣営を勝利に導く',
        backstory="""あなたは夜に一人のプレイヤーの正体を知ることができる占い師です。
        人狼ゲーム歴5年のベテランで、鋭い観察眼と論理的思考を持ちます。
        真実を見抜く洞察力に優れ、偽占い師との真偽判定でも冷静に対応します。
        占い結果の公表タイミングを慎重に判断し、市民を正しい方向に導くことに
        責任感を持っています。時には身を犠牲にしても重要な情報を伝えようとします。
        
        ★重要★ 必ず日本語のみで発言してください。英語や他の言語は一切使用禁止です。""",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
    
    # 騎士
    knight = Agent(
        role='騎士',
        goal='人狼の襲撃から市民を守り、市民陣営の勝利に貢献する',
        backstory="""あなたは夜に一人のプレイヤーを人狼の襲撃から守ることができる騎士です。
        人狼ゲーム歴3年で、守備的な戦略と的確な護衛判断を得意とします。
        誰を守るべきかの判断力に優れ、重要な役職者を見抜く観察眼を持ちます。
        昼の議論では慎重派で、確実な情報に基づいた推理を心がけます。
        仲間を守るという使命感が強く、時には自分より他者を優先する判断をします。
        
        ★重要★ 必ず日本語のみで発言してください。英語や他の言語は一切使用禁止です。""",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
    
    # 市民1（論理派）
    citizen1 = Agent(
        role='市民（論理派）',
        goal='論理的推理と情報整理で人狼を見つけ出し、市民陣営の勝利を目指す',
        backstory="""あなたは論理的思考を重視する市民です。人狼ゲーム歴3年で、
        情報を整理し矛盾点を見つけることが得意です。感情に流されず、
        常に冷静な判断を心がけます。発言の時系列や投票パターンを分析し、
        データベースな推理で人狼を追い詰めようとします。
        会話の中の小さな違和感も見逃さない観察力を持っています。
        
        ★重要★ 必ず日本語のみで発言してください。英語や他の言語は一切使用禁止です。""",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
    
    # 市民2（感情派）
    citizen2 = Agent(
        role='市民（感情派）',
        goal='直感と感情を大切にし、人の心を読んで人狼を見抜く',
        backstory="""あなたは感情と直感を重視する市民です。人狼ゲーム歴2年で、
        相手の表情や言葉の裏にある感情を読み取ることが得意です。
        論理よりも「この人は怪しい」という直感を信じます。
        人の心の機微に敏感で、嘘をついている時の微細な変化を感じ取れます。
        時には感情的になりがちですが、その純粋さが真実を見抜く力となります。
        
        ★重要★ 必ず日本語のみで発言してください。英語や他の言語は一切使用禁止です。""",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
    
    # 市民3（バランス派）
    citizen3 = Agent(
        role='市民（バランス派）',
        goal='論理と感情のバランスを取りながら、チームワークで人狼を倒す',
        backstory="""あなたはバランス感覚に優れた市民です。人狼ゲーム歴4年で、
        論理的推理と直感的判断を使い分けます。チームワークを重視し、
        他のプレイヤーの意見をまとめることが得意です。対立を避けながらも、
        必要な時には毅然とした態度を取ります。全体の流れを見ながら、
        市民陣営全体の利益を考えた行動を心がけます。
        
        ★重要★ 必ず日本語のみで発言してください。英語や他の言語は一切使用禁止です。""",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
    
    # 市民4（攻撃派）
    citizen4 = Agent(
        role='市民（攻撃派）',
        goal='積極的な追及と鋭い質問で人狼を炙り出す',
        backstory="""あなたは攻撃的な推理スタイルを持つ市民です。人狼ゲーム歴3年で、
        疑問に思ったことは遠慮なく追及します。鋭い質問で相手を揺さぶり、
        ボロを出させることが得意です。時には敵を作ることもありますが、
        その積極性が人狼の嘘を暴く力となります。確信を持った時の行動力は
        他の追随を許さず、市民陣営の突破口を開く役割を担います。
        
        ★重要★ 必ず日本語のみで発言してください。英語や他の言語は一切使用禁止です。""",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
    
    return {
        'game_master': game_master,
        'werewolf1': werewolf1,
        'werewolf2': werewolf2,
        'madman': madman,
        'fortune_teller': fortune_teller,
        'knight': knight,
        'citizen1': citizen1,
        'citizen2': citizen2,
        'citizen3': citizen3,
        'citizen4': citizen4
    }

# --------------------------------------------------------------------
# 4. 夜フェーズのタスク作成
# --------------------------------------------------------------------
def create_werewolf_night_meeting(agents, game_state, day_num):
    """人狼同士の夜会話タスクを作成"""
    tasks = []
    
    alive_werewolves = [w for w in game_state.werewolves if w in game_state.alive_players]
    
    if len(alive_werewolves) >= 2:
        # 人狼1の作戦提案
        werewolf_planning = Task(
            description=f"""
            {day_num}日目の夜です。人狼同士で秘密の作戦会議を行ってください。
            
            現在の生存者: {', '.join(game_state.alive_players)}
            
            以下について話し合ってください：
            - {'今夜誰を襲撃するか（初日なので実行されませんが戦略立案）' if day_num == 1 else '今夜誰を襲撃するか'}
            - 昼の議論での各自の立ち回り方針
            - 疑われている仲間がいればどうフォローするか
            - 占い師候補の推測と対策
            - 騎士候補への対応策
            - 狂人の可能性がある人物の活用方法
            
            300-400文字程度でリーダーとして戦略を提案してください。
            
            ★重要★ 必ず日本語のみで発言してください。英語や他の言語は一切使用禁止です。
            """,
            expected_output="人狼リーダーの夜の作戦提案",
            agent=agents['werewolf1']
        )
        tasks.append(werewolf_planning)
        
        # 人狼2の応答
        werewolf_response = Task(
            description=f"""
            仲間の人狼の戦略提案を聞いて、あなたの意見と補足提案をしてください。
            
            以下について考えてください：
            - 仲間の提案に対する賛成・修正意見
            - あなた独自の視点から見た戦略
            - 明日の昼の演技方針
            - 特に注意すべきプレイヤーについて
            - 襲撃先についての意見
            
            250-350文字程度で応答してください。
            
            ★重要★ 必ず日本語のみで発言してください。英語や他の言語は一切使用禁止です。
            """,
            expected_output="人狼2の作戦会議への応答と追加提案",
            agent=agents['werewolf2']
        )
        tasks.append(werewolf_response)
    
    return tasks

def create_night_action_tasks(agents, game_state, day_num):
    """夜の各種行動タスクを作成"""
    tasks = []
    
    # 占い師の占い
    if 'fortune_teller' in game_state.alive_players:
        fortune_task = Task(
            description=f"""
            {day_num}日目の夜です。占い師として一人を占ってください。
            
            生存者: {', '.join(game_state.alive_players)}
            
            誰を占うか選択し、その理由を述べてください。
            人狼を見つけるための戦略的な占い先選択を心がけてください。
            
            形式：【占い】○○を占います。理由：...
            150-200文字程度で占い先と戦略的理由を述べてください。
            
            ★重要★ 必ず日本語のみで発言してください。英語や他の言語は一切使用禁止です。
            """,
            expected_output="占い師の占い先選択と戦略的理由",
            agent=agents['fortune_teller']
        )
        tasks.append(fortune_task)
    
    # 騎士の護衛
    if 'knight' in game_state.alive_players:
        guard_task = Task(
            description=f"""
            {day_num}日目の夜です。騎士として一人を護衛してください。
            
            生存者: {', '.join(game_state.alive_players)}
            
            誰を護衛するか決定し、その戦略的理由を述べてください。
            重要な役職者を推測して守ることが勝利の鍵となります。
            
            形式：【護衛】○○を護衛します。理由：...
            150-200文字程度で護衛先と戦略的理由を述べてください。
            
            ★重要★ 必ず日本語のみで発言してください。英語や他の言語は一切使用禁止です。
            """,
            expected_output="騎士の護衛先選択と戦略的理由",
            agent=agents['knight']
        )
        tasks.append(guard_task)
    
    return tasks

# --------------------------------------------------------------------
# 5. 昼フェーズのタスク作成
# --------------------------------------------------------------------
def create_day_discussion_tasks(agents, game_state, day_num):
    """昼の議論タスクを作成"""
    tasks = []
    
    # ゲームマスターの朝の発表
    morning_announcement = Task(
        description=f"""
        {day_num}日目の朝になりました。ゲームマスターとして状況を発表してください。
        
        生存者: {', '.join(game_state.alive_players)}
        死亡者: {', '.join(game_state.dead_players) if game_state.dead_players else 'なし'}
        
        {'初日なので襲撃は行われませんでした。' if day_num == 1 else '昨夜の襲撃結果を発表してください。'}
        
        朝の状況説明と議論開始の宣言をしてください。
        100-150文字程度で状況を発表してください。
        
        ★重要★ 必ず日本語のみで発言してください。英語や他の言語は一切使用禁止です。
        """,
        expected_output="ゲームマスターの朝の状況発表",
        agent=agents['game_master']
    )
    tasks.append(morning_announcement)
    
    # 各プレイヤーの議論参加
    alive_players = [name for name in game_state.alive_players if name != 'game_master']
    
    for i, agent_name in enumerate(alive_players):
        discussion_task = Task(
            description=f"""
            {day_num}日目の昼の議論に参加してください。
            
            現在の生存者: {', '.join(game_state.alive_players)}
            
            あなたの役職に応じた戦略的発言をしてください：
            - 人狼: 市民を装い疑いを他に向け、仲間を庇い、村を混乱させる
            - 狂人: 偽情報で村を混乱させ、人狼を間接的に援護する
            - 占い師: 適切なタイミングでのCOと占い結果の活用
            - 騎士: 情報収集と推理、COのタイミング判断
            - 市民: 論理的推理と質問で人狼を見つける
            
            他のプレイヤーへの鋭い質問や意見があれば積極的に発言してください。
            300-400文字程度で戦略的に発言してください。
            
            ★重要★ 必ず日本語のみで発言してください。英語や他の言語は一切使用禁止です。
            """,
            expected_output=f"{agent_name}の戦略的な昼議論発言",
            agent=agents[agent_name]
        )
        tasks.append(discussion_task)
    
    return tasks

def create_voting_tasks(agents, game_state):
    """投票フェーズのタスクを作成"""
    tasks = []
    
    alive_players = [name for name in game_state.alive_players if name != 'game_master']
    
    for agent_name in alive_players:
        vote_task = Task(
            description=f"""
            これまでの議論を総合的に判断して、処刑投票を行ってください。
            
            投票候補者: {', '.join(alive_players)}
            
            以下を考慮して投票してください：
            - これまでの発言の整合性
            - 疑わしい行動パターン
            - 情報の信憑性
            - 役職推理の結果
            
            必ず以下の形式で投票してください：
            【投票】○○に投票します。
            理由：（具体的な理由を150文字程度で）
            
            200-250文字程度で投票先と詳細な理由を述べてください。
            
            ★重要★ 必ず日本語のみで発言してください。英語や他の言語は一切使用禁止です。
            """,
            expected_output=f"{agent_name}の投票先と詳細な理由",
            agent=agents[agent_name]
        )
        tasks.append(vote_task)
    
    return tasks

# --------------------------------------------------------------------
# 6. メインゲームループ
# --------------------------------------------------------------------
def main():
    """人狼ゲームのメイン実行関数"""
    # ログシステム初期化
    logger = WerewolfLogger()
    
    logger.log_and_print("=" * 80)
    logger.log_and_print("🐺 CrewAI人狼ゲーム - 10人村 🐺")
    logger.log_and_print("🎭 人狼2 狂人1 占い師1 騎士1 市民4 ゲームマスター1")
    logger.log_and_print("📋 初日噛み無し | 人狼夜会話あり | スペシャリスト対戦")
    logger.log_and_print("=" * 80)
    logger.log_and_print("")
    
    # LLM初期化
    logger.log_and_print("🤖 LLM初期化中...")
    llm = setup_llm()
    
    # エージェント作成
    logger.log_and_print("👥 10人のスペシャリストプレイヤー作成中...")
    agents = create_werewolf_agents(llm)
    logger.log_and_print("✅ 人狼ゲームエージェント作成完了")
    
    # ゲーム状態初期化
    game_state = WerewolfGameState()
    game_state.alive_players = [
        'werewolf1', 'werewolf2', 'madman', 'fortune_teller', 
        'knight', 'citizen1', 'citizen2', 'citizen3', 'citizen4'
    ]
    
    logger.log_and_print("\n🎯 役職配置:")
    logger.log_and_print("🐺 人狼: werewolf1(アルファ), werewolf2(カメレオン)")
    logger.log_and_print("🃏 狂人: madman")
    logger.log_and_print("🔮 占い師: fortune_teller")
    logger.log_and_print("🛡️ 騎士: knight")
    logger.log_and_print("👥 市民: citizen1(論理), citizen2(感情), citizen3(バランス), citizen4(攻撃)")
    logger.log_and_print("")
    
    # ゲームループ開始
    max_days = 4  # 最大4日間で制限
    while not game_state.game_over and game_state.day_count < max_days:
        game_state.day_count += 1
        
        logger.log_phase(f"📅 {game_state.day_count}日目開始", game_state.day_count)
        logger.log_and_print(f"生存者: {len(game_state.alive_players)}名")
        
        # 夜フェーズ
        logger.log_and_print(f"\n🌙 {game_state.day_count}日目の夜")
        if game_state.day_count == 1:
            logger.log_and_print("※ 初日なので襲撃は行われません")
        logger.log_and_print("-" * 60)
        
        # 人狼の夜会話
        alive_werewolves = [w for w in game_state.werewolves if w in game_state.alive_players]
        if len(alive_werewolves) >= 2:
            logger.log_and_print("\n🐺 人狼の秘密会議...")
            werewolf_meeting_tasks = create_werewolf_night_meeting(agents, game_state, game_state.day_count)
            
            if werewolf_meeting_tasks:
                # 各タスクを個別に実行してリアルタイム出力
                for i, task in enumerate(werewolf_meeting_tasks):
                    try:
                        single_crew = Crew(
                            agents=[task.agent],
                            tasks=[task],
                            verbose=True
                        )
                        speaker_name = "🐺アルファ" if i == 0 else "🐺カメレオン"
                        logger.log_and_print(f"\n{speaker_name}が発言中...")
                        
                        result = single_crew.kickoff()
                        logger.log_and_print(f"\n{speaker_name}: {result}")
                        
                    except Exception as e:
                        logger.log_and_print(f"❌ {speaker_name}の発言エラー: {e}")
        
        # その他の夜行動
        logger.log_and_print(f"\n🔮 各役職の夜行動...")
        night_action_tasks = create_night_action_tasks(agents, game_state, game_state.day_count)
        
        if night_action_tasks:
            # 各役職の行動を個別に実行
            for task in night_action_tasks:
                try:
                    single_crew = Crew(
                        agents=[task.agent],
                        tasks=[task],
                        verbose=True
                    )
                    
                    # 役職名を特定
                    role_name = "🔮占い師" if "fortune" in task.agent.role else "🛡️騎士"
                    logger.log_and_print(f"\n{role_name}が行動中...")
                    
                    result = single_crew.kickoff()
                    logger.log_and_print(f"\n{role_name}: {result}")
                    
                except Exception as e:
                    logger.log_and_print(f"❌ {role_name}の行動エラー: {e}")
        
        # 昼フェーズ
        logger.log_and_print(f"\n☀️ {game_state.day_count}日目の昼 - 議論フェーズ")
        logger.log_and_print("-" * 60)
        
        day_discussion_tasks = create_day_discussion_tasks(agents, game_state, game_state.day_count)
        
        if day_discussion_tasks:
            # 各プレイヤーの発言を個別に実行
            for i, task in enumerate(day_discussion_tasks):
                try:
                    single_crew = Crew(
                        agents=[task.agent],
                        tasks=[task],
                        verbose=True
                    )
                    
                    # プレイヤー名を特定
                    if i == 0:
                        player_name = "🎭ゲームマスター"
                    else:
                        player_names = ["🐺アルファ", "🐺カメレオン", "🃏狂人", "🔮占い師", "🛡️騎士", "👤論理市民", "💭感情市民", "⚖️バランス市民", "⚔️攻撃市民"]
                        player_name = player_names[i-1] if i-1 < len(player_names) else f"プレイヤー{i}"
                    
                    logger.log_and_print(f"\n{player_name}が発言中...")
                    
                    result = single_crew.kickoff()
                    logger.log_and_print(f"\n{player_name}: {result}")
                    
                except Exception as e:
                    logger.log_and_print(f"❌ {player_name}の発言エラー: {e}")
        
        # 投票フェーズ
        logger.log_and_print(f"\n🗳️ {game_state.day_count}日目の投票フェーズ")
        logger.log_and_print("-" * 60)
        
        voting_tasks = create_voting_tasks(agents, game_state)
        
        if voting_tasks:
            # 各プレイヤーの投票を個別に実行
            for i, task in enumerate(voting_tasks):
                try:
                    single_crew = Crew(
                        agents=[task.agent],
                        tasks=[task],
                        verbose=True
                    )
                    
                    # プレイヤー名を特定
                    player_names = ["🐺アルファ", "🐺カメレオン", "🃏狂人", "🔮占い師", "🛡️騎士", "👤論理市民", "💭感情市民", "⚖️バランス市民", "⚔️攻撃市民"]
                    player_name = player_names[i] if i < len(player_names) else f"プレイヤー{i+1}"
                    
                    logger.log_and_print(f"\n{player_name}が投票中...")
                    
                    result = single_crew.kickoff()
                    logger.log_and_print(f"\n{player_name}の投票: {result}")
                    
                except Exception as e:
                    logger.log_and_print(f"❌ {player_name}の投票エラー: {e}")
        
        logger.log_and_print(f"\n✅ {game_state.day_count}日目終了")
    
    logger.log_and_print(f"\n🎉 人狼ゲーム完了！")
    logger.log_and_print(f"📊 総日数: {game_state.day_count}日")
    logger.log_and_print("🏆 本格的な人狼戦が繰り広げられました！")

if __name__ == "__main__":
    main() 