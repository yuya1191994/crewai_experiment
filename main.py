import os
from crewai import Agent, Task, Crew, LLM

# --------------------------------------------------------------------
# 1. LLM（大規模言語モデル）のセットアップ
# --------------------------------------------------------------------
def setup_llm():
    """Gemini LLMを初期化"""
    try:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY環境変数が設定されていません")
        
        # CrewAI独自のLLM設定でGeminiを使用
        llm = LLM(
            model="gemini/gemini-1.5-flash",
            api_key=api_key
        )
        print("✅ LLM初期化成功")
        return llm
    except Exception as e:
        print(f"❌ LLM初期化エラー: {e}")
        exit(1)

# --------------------------------------------------------------------
# 2. シンプルなエージェント作成（まずは1人でテスト）
# --------------------------------------------------------------------
def create_simple_agent(llm):
    """シンプルなテストエージェントを作成"""
    
    agent = Agent(
        role="AI Discussion Facilitator",
        goal="AI時代のエンジニアキャリアについて考察し、議論をまとめる",
        backstory="""
        あなたはAI時代のエンジニアキャリアについて詳しい専門家です。
        4人のエンジニア（3人のシニア + 1人のジュニア）の視点から、
        AI時代におけるエンジニアの価値について議論をまとめることができます。
        """,
        verbose=False,
        allow_delegation=False,
        llm=llm
    )
    
    return agent

# --------------------------------------------------------------------
# 3. シンプルなタスク作成
# --------------------------------------------------------------------
def create_simple_task(agent):
    """シンプルなディスカッションタスクを作成"""
    
    task = Task(
        description="""
        AI時代のエンジニアキャリアについて、以下の4人の視点から議論をまとめてください：

        1. 田中さん (40代・シニアエンジニア): システム設計が専門。AIによるコード生成の影響を心配している
        2. 佐藤さん (30代・バックエンドエンジニア): インフラ自動化の進歩で自分の価値が下がることを懸念
        3. 山田さん (40代・フロントエンドエンジニア): AI生成UIツールの台頭で創造性の価値を問い直している  
        4. 鈴木さん (20代・ジュニアエンジニア): AIに仕事を奪われるのではないかと不安を感じている

        この4人が以下のテーマについて議論する内容を作成してください：
        - AI時代におけるエンジニアの真の価値とは？
        - 今後求められるスキルや役割の変化
        - AIと共存するための学習戦略

        対話形式で自然な会話として表現してください。
        """,
        expected_output="""
        4人のエンジニアによる自然な対話形式のディスカッション。
        各人の専門性と立場が反映された発言で構成された、
        2000文字程度の充実した議論内容。
        """,
        agent=agent
    )
    
    return task

# --------------------------------------------------------------------
# 4. メイン実行部分
# --------------------------------------------------------------------
def main():
    """メイン実行関数"""
    print("=" * 60)
    print("🤖 AI時代のデベロッパーキャリア ディスカッション")
    print("👥 シンプル版テスト")
    print("=" * 60)
    print()
    
    # LLMセットアップ
    llm = setup_llm()
    
    # エージェント作成
    print("👤 エージェント作成中...")
    agent = create_simple_agent(llm)
    print("✅ エージェントを作成しました")
    
    # タスク作成
    print("📋 ディスカッションタスク作成中...")
    task = create_simple_task(agent)
    print("✅ タスクを作成しました")
    
    # クルー作成
    print("🚀 クルー結成中...")
    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=False
    )
    print("✅ クルーを結成しました")
    
    # ディスカッション実行
    print("\n🎯 ディスカッション開始...")
    print("-" * 60)
    
    try:
        result = crew.kickoff()
        
        print("\n" + "=" * 60)
        print("🎉 ディスカッション完了！")
        print("=" * 60)
        print("\n📝 ディスカッション結果:")
        print("-" * 60)
        print(result)
        print("-" * 60)
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        print("\n🔍 詳細なエラー情報:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()



