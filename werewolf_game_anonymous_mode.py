# CrewAI人狼ゲーム - 10人村（匿名モード）
import os
import random
import datetime
import re
from crewai import Agent, Task, Crew, LLM

# --------------------------------------------------------------------
# 1. ユーティリティ関数
# --------------------------------------------------------------------
def extract_clean_speech(raw_output):
    """CrewAIの出力から思考過程を除去し、日本語の発言部分のみ抽出"""
    output_str = str(raw_output).strip()
    
    # まず空文字チェック
    if not output_str:
        return "（発言なし）"
    
    # "Thought:"が含まれている場合、思考部分を除去
    if "Thought:" in output_str:
        # "Thought:"以降の部分を除去
        clean_output = output_str.split("Thought:")[0].strip()
        if clean_output:
            return clean_output
    
    # 英語の一般的なフレーズを除去
    patterns_to_remove = [
        r'Agent Final Answer:.*?(?=\n|$)',
        r'Final Answer:.*?(?=\n|$)',  
        r'Action:.*?(?=\n|$)',
        r'Observation:.*?(?=\n|$)',
        r'I need to.*?(?=\n|$)',
        r'Based on.*?(?=\n|$)'
    ]
    
    cleaned = output_str
    for pattern in patterns_to_remove:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.DOTALL)
    
    # 改行で分割して日本語が含まれる行のみを保持
    lines = cleaned.split('\n')
    japanese_lines = []
    
    for line in lines:
        line = line.strip()
        if line and re.search(r'[ひらがなカタカナ漢字]', line):
            japanese_lines.append(line)
    
    if japanese_lines:
        return '\n'.join(japanese_lines)
    
    # 日本語が見つからない場合でも、空でなければそのまま返す
    cleaned = cleaned.strip()
    if cleaned:
        return cleaned
    
    return "（発言なし）"

# --------------------------------------------------------------------
# 2. LLM（大規模言語モデル）のセットアップ
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
        self.log_file = f"warewolf_logs/anonymous_mode_{timestamp_str}.md"
        
        # ログファイルを初期化
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(f"🎭 CrewAI人狼ゲーム（匿名モード） ログ - {timestamp.strftime('%Y%m%d%H%M%S')}\n")
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
        
        # ランダム化された役職配置（実行時まで不明）
        self.werewolves = []
        self.madman = None
        self.fortune_teller = None
        self.knight = None
        self.citizens = []
        
        # 占い・護衛結果
        self.fortune_results = []
        self.protected_player = None
        
        # プレイヤー名マッピング（ランダム化）
        self.player_role_mapping = {}
        self.role_player_mapping = {}

def setup_random_roles(game_state):
    """役職をランダムに配置する"""
    # 日本人のひらがな名前リスト
    possible_names = [
        'たろう', 'はなこ', 'けんじ', 'あやか', 'ひろし', 
        'みさき', 'だいすけ', 'ゆり', 'まさき', 'あい',
        'りょうた', 'まお', 'しゅん', 'みき', 'かずや',
        'さくら', 'とものり', 'みゆき', 'こうた', 'なな'
    ]
    
    # 9つの名前をランダム選択
    selected_names = random.sample(possible_names, 9)
    
    # 役職リストを作成
    roles = ['werewolf'] * 2 + ['madman'] + ['fortune_teller'] + ['knight'] + ['citizen'] * 4
    
    # シャッフル
    random.shuffle(roles)
    
    # 役職とプレイヤー名をマッピング
    for i, (name, role) in enumerate(zip(selected_names, roles)):
        game_state.player_role_mapping[name] = role
        game_state.role_player_mapping[role] = game_state.role_player_mapping.get(role, []) + [name]
    
    # ゲーム状態に反映
    werewolf_players = [name for name, role in game_state.player_role_mapping.items() if role == 'werewolf']
    game_state.werewolves = werewolf_players
    game_state.madman = next(name for name, role in game_state.player_role_mapping.items() if role == 'madman')
    game_state.fortune_teller = next(name for name, role in game_state.player_role_mapping.items() if role == 'fortune_teller')
    game_state.knight = next(name for name, role in game_state.player_role_mapping.items() if role == 'knight')
    game_state.citizens = [name for name, role in game_state.player_role_mapping.items() if role == 'citizen']
    
    # 生存者リストを設定
    game_state.alive_players = selected_names
    
    return selected_names

# --------------------------------------------------------------------
# 4. 匿名化されたエージェント作成
# --------------------------------------------------------------------
def create_werewolf_agents(llm, player_names):
    """人狼ゲームの各プレイヤーエージェントを作成（ランダム名前版）"""
    agents = {}
    
    # プレイヤー性格パターン
    personalities = [
        ("論理的思考", "冷静沈着で戦略的思考に優れ、論理的な推理と分析を得意とします"),
        ("演技力・心理戦", "卓越した演技力を持ち、相手の心を読み取ることが得意です"),
        ("大胆・予測不能", "常識にとらわれない発想と行動力で、予測不可能な行動を取ります"),
        ("鋭い洞察力", "細かな言動の変化を見逃さず、矛盾点を的確に指摘できます"),
        ("守備的・支援型", "慎重な分析と確実な情報収集を得意とし、チーム全体を重視します"),
        ("論理分析型", "情報整理と矛盾点発見が得意で、データに基づいた推理を行います"),
        ("感情・直感型", "相手の感情を読み取り、直感を信じて判断することが得意です"),
        ("バランス型", "論理と直感を使い分け、他プレイヤーの意見をまとめるのが得意です"),
        ("攻撃的追及型", "疑問点を遠慮なく追及し、鋭い質問で相手を揺さぶります")
    ]
    
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
    agents['game_master'] = game_master
    
    # ランダムなプレイヤーたちを作成
    for i, name in enumerate(player_names):
        personality_name, personality_desc = personalities[i]
        
        agent = Agent(
            role=f'{name}',
            goal='戦略的思考と推理力で勝利を目指す',
            backstory=f"""あなたは{personality_desc}。人狼ゲーム歴{random.randint(2,5)}年のプレイヤーで、
            {personality_name}のスタイルで他のプレイヤーとの駆け引きを楽しみます。
            勝利に向けて最適な戦略を練り、場の流れを読みながら行動します。
            
            ★重要★ 必ず日本語のみで発言してください。英語や他の言語は一切使用禁止です。""",
            verbose=True,
            allow_delegation=False,
            llm=llm
        )
        agents[name] = agent
    
    return agents

# --------------------------------------------------------------------
# 5. 夜の行動タスク作成（人狼会話は非表示）
# --------------------------------------------------------------------
def create_night_action_tasks(agents, game_state, day_num):
    """夜の各種行動タスクを作成（ランダム役職対応）"""
    tasks = []
    
    # 占い師の占い
    if game_state.fortune_teller and game_state.fortune_teller in game_state.alive_players:
        fortune_task = Task(
            description=f"""
            {day_num}日目の夜です。一人を選んで特別な調査を行ってください。
            
            生存者: {', '.join(game_state.alive_players)}
            
            誰を調査するか選択し、その戦略的理由を述べてください。
            慎重な判断が重要です。
            
            形式：【調査】○○を調査します。理由：...
            150-200文字程度で調査先と戦略的理由を述べてください。
            
            ★重要★ 必ず日本語のみで発言してください。英語や他の言語は一切使用禁止です。
            """,
            expected_output="占い師の調査先選択と戦略的理由",
            agent=agents[game_state.fortune_teller]
        )
        tasks.append(fortune_task)
    
    # 騎士の護衛
    if game_state.knight and game_state.knight in game_state.alive_players:
        guard_task = Task(
            description=f"""
            {day_num}日目の夜です。一人を選んで特別な保護を行ってください。
            
            生存者: {', '.join(game_state.alive_players)}
            
            誰を保護するか決定し、その戦略的理由を述べてください。
            重要な人物を守ることが勝利の鍵となるかもしれません。
            
            形式：【保護】○○を保護します。理由：...
            150-200文字程度で保護先と戦略的理由を述べてください。
            
            ★重要★ 必ず日本語のみで発言してください。英語や他の言語は一切使用禁止です。
            """,
            expected_output="騎士の護衛先選択と戦略的理由",
            agent=agents[game_state.knight]
        )
        tasks.append(guard_task)
    
    return tasks

# --------------------------------------------------------------------
# 6. 昼フェーズのタスク作成
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
        
        {'初日なので特別な出来事はありませんでした。' if day_num == 1 else '昨夜の結果を発表してください。'}
        
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
            
            他のプレイヤーの発言を注意深く聞き、推理と意見を述べてください。
            - 疑わしいと思う相手への質問
            - これまでの発言の矛盾点の指摘
            - 自分なりの推理の発表
            - 重要だと思う情報があれば共有
            
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
            - 全体的な推理の結果
            
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
# 7. メインゲームループ
# --------------------------------------------------------------------
def main():
    """人狼ゲームのメイン実行関数（匿名モード）"""
    # ログシステム初期化
    logger = WerewolfLogger()
    
    logger.log_and_print("=" * 80)
    logger.log_and_print("🎭 CrewAI人狼ゲーム - 10人村（匿名モード）🎭")
    logger.log_and_print("🕵️ 誰が人狼なのか推理しながら観戦しよう！")
    logger.log_and_print("📋 初日噛み無し | 人狼夜会話非表示 | 参加型観戦")
    logger.log_and_print("=" * 80)
    logger.log_and_print("")
    
    # LLM初期化
    logger.log_and_print("🤖 LLM初期化中...")
    llm = setup_llm()
    
    # ゲーム状態初期化とランダム役職配置
    logger.log_and_print("🎲 ランダム役職配置中...")
    game_state = WerewolfGameState()
    player_names = setup_random_roles(game_state)
    
    # エージェント作成
    logger.log_and_print("👥 9人の匿名プレイヤー作成中...")
    agents = create_werewolf_agents(llm, player_names)
    logger.log_and_print("✅ 人狼ゲームエージェント作成完了")
    
    logger.log_and_print("\n🎯 今回のプレイヤー構成:")
    for name in player_names:
        logger.log_and_print(f"👤 {name}さん")
    logger.log_and_print("")
    logger.log_and_print("🔍 役職は完全にランダム配置されました！")
    logger.log_and_print("🐺 人狼2名 | 🃏 狂人1名 | 🔮 占い師1名 | 🛡️ 騎士1名 | 👥 市民4名")
    logger.log_and_print("📝 ソースコードを読んでも役職配置はわかりません！")
    logger.log_and_print("")
    
    # ゲームループ開始
    max_days = 4  # 最大4日間で制限
    while not game_state.game_over and game_state.day_count < max_days:
        game_state.day_count += 1
        
        logger.log_phase(f"📅 {game_state.day_count}日目開始", game_state.day_count)
        logger.log_and_print(f"生存者: {len(game_state.alive_players)}名")
        
        # 夜フェーズ（人狼会話は非表示）
        logger.log_and_print(f"\n🌙 {game_state.day_count}日目の夜")
        if game_state.day_count == 1:
            logger.log_and_print("※ 初日なので襲撃は行われません")
        logger.log_and_print("※ 人狼の会話は見えません...")
        logger.log_and_print("-" * 60)
        
        # 夜の行動（完全秘匿実行）
        logger.log_and_print(f"\n🌙 夜が更けていきます...")
        logger.log_and_print("💤 村は静寂に包まれています...")
        logger.log_and_print("🌟 何かが起こっているかもしれませんが、誰にもわかりません...")
        
        night_action_tasks = create_night_action_tasks(agents, game_state, game_state.day_count)
        
        if night_action_tasks:
            # 完全に裏で実行（一切の情報を隠蔽）
            for task in night_action_tasks:
                try:
                    single_crew = Crew(
                        agents=[task.agent],
                        tasks=[task],
                        verbose=False
                    )
                    result = single_crew.kickoff()
                    # 結果は内部処理のみ、一切表示しない
                except Exception as e:
                    # エラーも隠蔽（ゲームの公平性のため）
                    pass
        
        logger.log_and_print("🌅 夜が明けようとしています...")
        
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
                        verbose=False  # Agent Final Answerを隠すため
                    )
                    
                    # プレイヤー名を特定
                    if i == 0:
                        player_name = "🎭ゲームマスター"
                    else:
                        current_players = [name for name in game_state.alive_players if name != 'game_master']
                        player_name = f"👤{current_players[i-1]}さん" if i-1 < len(current_players) else f"プレイヤー{i}"
                    
                    logger.log_and_print(f"\n{player_name}が発言中...")
                    
                    result = single_crew.kickoff()
                    # 思考過程を除去してクリーンな発言のみ抽出
                    clean_result = extract_clean_speech(str(result))
                    logger.log_and_print(f"\n{player_name}: {clean_result}")
                    
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
                        verbose=False  # Agent Final Answerを隠すため
                    )
                    
                    # プレイヤー名を特定
                    current_players = [name for name in game_state.alive_players if name != 'game_master']
                    player_name = f"👤{current_players[i]}さん" if i < len(current_players) else f"プレイヤー{i+1}"
                    
                    logger.log_and_print(f"\n{player_name}が投票中...")
                    
                    result = single_crew.kickoff()
                    # 思考過程を除去してクリーンな投票のみ抽出
                    clean_result = extract_clean_speech(str(result))
                    logger.log_and_print(f"\n{player_name}の投票: {clean_result}")
                    
                except Exception as e:
                    logger.log_and_print(f"❌ {player_name}の投票エラー: {e}")
        
        logger.log_and_print(f"\n✅ {game_state.day_count}日目終了")
    
    logger.log_and_print(f"\n🎉 人狼ゲーム完了！")
    logger.log_and_print(f"📊 総日数: {game_state.day_count}日")
    logger.log_and_print("🕵️ さあ、あなたの推理は当たっていましたか？")
    logger.log_and_print("\n🔍 答え合わせ:")
    logger.log_and_print(f"🐺 人狼: {', '.join([f'{w}さん' for w in game_state.werewolves])}")
    logger.log_and_print(f"🃏 狂人: {game_state.madman}さん")
    logger.log_and_print(f"🔮 占い師: {game_state.fortune_teller}さん")
    logger.log_and_print(f"🛡️ 騎士: {game_state.knight}さん")
    logger.log_and_print(f"👥 市民: {', '.join([f'{c}さん' for c in game_state.citizens])}")

if __name__ == "__main__":
    main()
